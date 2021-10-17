"""
Project name: Commit Message Bot
Written by: Phillip Tat
Date written: 8/23/21
For: UCF Senior Design Project
Purpose: Help evaluate commit messages through a likes system.
"""
import os, aiohttp, base64
from aiohttp import web
from gidgethub import routing, sansio
from gidgethub import aiohttp as gh_aiohttp
from pymongo import MongoClient
from datetime import datetime

router = routing.Router()
routes = web.RouteTableDef()

@router.register("push")
async def push_event(event, gh, db, *args, **kwargs):
    # data collection of push payload
    repo_owner = event.data["repository"]["owner"]["login"]
    repo_full_name = event.data["repository"]["full_name"]
    repo_name = event.data["repository"]["name"]
    repo_id = event.data["repository"]["id"]
    repo_url = event.data["repository"]["html_url"]
    username = event.data["sender"]["login"]
    user_id = event.data["sender"]["id"]
    likes = 0
    num_commits = len(event.data["commits"])
    # store the commit data into lists
    commits = []
    # check whether commit is distinct
    non_distinct_commit = 0

    for comm in event.data["commits"]:
        commits.append({
            "commit_id": comm["id"],
            "distinct": comm["distinct"],
            "commit_time": comm["timestamp"]
        })
        # keep count of number of commits that are not distinct
        if not comm["distinct"]:
            non_distinct_commit += 1

    # remove non_distinct_commits from num_commits
    num_commits = num_commits - non_distinct_commit

    # create the data collection payload
    payload = {
        "repo_owner": repo_owner,
        "repo_full_name": repo_full_name,
        "repo_name": repo_name,
        "repo_id": repo_id,
        "repo_url": repo_url,
        "username": username,
        "user_id": user_id,
        "likes": likes,
        "num_commits": num_commits,
        "commits": commits
    }
    # find user in user_commits
    user = db.user_commits.find_one({"repo_full_name": repo_full_name, "username": username})

    if user == None:
        db.user_commits.insert_one(payload)
    else:


# end of push_event

@routes.post("/")
async def main(request):
    # read the github webhook payload
    body = await request.read()

    # our authentication token and secret
    secret = os.environ.get("GH_SECRET")
    oauth_token = os.environ.get("GH_AUTH")
    # our mongodb uri with username and password
    uri = os.environ.get("MONGODB_URI")
    client = MongoClient(uri)
    # connect to test db
    db = client.test

    # a representation of github webhook event
    event = sansio.Event.from_http(request.headers, body, secret = secret)

    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(session, "PtatG", oauth_token = oauth_token)
        await router.dispatch(event, gh, db)

    return web.Response(status = 200)

if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)

    web.run_app(app, port = port)
