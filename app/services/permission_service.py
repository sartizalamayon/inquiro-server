# app/services/permission_service.py

from typing import List, Union, Literal
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.permission import PermissionDoc, PermissionCreate, UserSummary
from app.database.mongodb import get_database
from fastapi import Depends

AccessLevel = Literal["scan", "modify", "control"]

async def grant_permission(
    db: AsyncIOMotorDatabase,
    data: PermissionCreate,
    granted_by: str
) -> PermissionDoc:
    """
    Upsert a permission for a given collection and user.
    """
    now = datetime.utcnow()
    await db["permissions"].update_one(
        {"collection_id": data.collection_id, "user_email": data.user_email},
        {"$set": {
            "access_level": data.access_level,
            "granted_by": granted_by,
            "granted_at": now,
        }},
        upsert=True,
    )
    raw = await db["permissions"].find_one({
        "collection_id": data.collection_id,
        "user_email": data.user_email
    })
    # Convert ObjectId fields to str for Pydantic
    doc = {
        **raw,
        "_id": str(raw["_id"]),
        "collection_id": str(raw["collection_id"]),
    }
    return PermissionDoc(**doc)


async def update_permission(
    db: AsyncIOMotorDatabase,
    collection_id: str,
    user_email: str,
    access_level: str,
    granted_by: str
) -> PermissionDoc:
    """
    Update an existing permission for a given collection and user.
    If the permission does not exist, it will not be created.
    """
    now = datetime.utcnow()
    result = await db["permissions"].update_one(
        {"collection_id": collection_id, "user_email": user_email},
        {"$set": {
            "access_level": access_level,
            "granted_by": granted_by,
            "granted_at": now,  # Update the timestamp to reflect the change
        }}
    )

    if result.matched_count == 0:
        # Optionally, raise an error or handle cases where the permission doesn't exist
        # For now, we'll assume the controller handles non-existent permissions (e.g., with a 404)
        # or that an update to a non-existent permission is a no-op that returns None or raises.
        # Let's make it return the updated doc or raise if not found.
        raise ValueError("Permission not found for update.")


    raw = await db["permissions"].find_one({
        "collection_id": collection_id,
        "user_email": user_email
    })
    if not raw:
        # This case should ideally not be reached if result.matched_count > 0
        # but as a safeguard:
        raise ValueError("Permission disappeared after update.")

    doc = {
        **raw,
        "_id": str(raw["_id"]),
        "collection_id": str(raw["collection_id"]),
    }
    return PermissionDoc(**doc)


async def revoke_permission(
    db: AsyncIOMotorDatabase,
    collection_id: str,
    user_email: str
) -> None:
    """
    Remove any permission for this user on this collection.
    """
    await db["permissions"].delete_one({
        "collection_id": collection_id,
        "user_email": user_email
    })
    


async def list_permissions_for_collection(
    db: AsyncIOMotorDatabase,
    collection_id: str
) -> List[PermissionDoc]:
    """
    Return all PermissionDoc entries for a given collection.
    """
    raws = await db["permissions"].find(
        {"collection_id": collection_id}
    ).to_list(None)

    out: List[PermissionDoc] = []
    for raw in raws:
        d = {
            **raw,
            "_id": str(raw["_id"]),
            "collection_id": str(raw["collection_id"]),
        }
        out.append(PermissionDoc(**d))
    return out


async def list_collections_for_user(
    db: AsyncIOMotorDatabase,
    user_email: str
) -> List[PermissionDoc]:
    """
    Return all PermissionDoc entries granted to a given user.
    """
    raws = await db["permissions"].find(
        {"user_email": user_email}
    ).to_list(None)

    out: List[PermissionDoc] = []
    for raw in raws:
        d = {
            **raw,
            "_id": str(raw["_id"]),
            "collection_id": str(raw["collection_id"]),
        }
        out.append(PermissionDoc(**d))
    return out


async def get_paper_access(
    db: AsyncIOMotorDatabase,
    paper_id: str,
    user_email: str,
) -> Union[AccessLevel, Literal["none"]]:
    """
    Determine the highest access level ('scan'/'modify'/'control')
    that `user_email` has for the given paper, or 'none' if no access.
    """

    # 1) Paper owner always has control
    paper = await db["papers"].find_one({"_id": ObjectId(paper_id)})
    if not paper:
        return "none"
    if paper.get("user_email") == user_email:
        return "control"

    # 2) Collection owner (of any collection containing this paper) also has control
    owner_coll = await db["collections"].find_one({
        "user_email": user_email,
        "papers": paper_id         # <-- string match, since collections.papers is string[]
    })
    if owner_coll:
        return "control"

    # 3) Otherwise check explicit share-permissions:
    #    a) Find all collections (by their _id) that list this paper
    coll_cursor = db["collections"].find(
        {"papers": paper_id},     # <-- string match
        {"_id": 1}
    )
    coll_ids = [str(c["_id"]) async for c in coll_cursor]
    if not coll_ids:
        return "none"

    #    b) Look up any PermissionDocs for this user on those collections
    perm_cursor = db["permissions"].find({
        "collection_id": {"$in": coll_ids},
        "user_email": user_email
    })
    levels = [d["access_level"] async for d in perm_cursor]

    # 4) Pick the highest privilege among them
    order = {"scan": 1, "modify": 2, "control": 3}
    best = "none"
    best_val = 0
    for lvl in levels:
        val = order.get(lvl, 0)
        if val > best_val:
            best_val = val
            best = lvl

    return best


async def get_users_with_access(
    collection_id: str,
    db: AsyncIOMotorDatabase
) -> List[UserSummary]: # Return type is now List[UserSummary]
    """
    List all users (name + email + access_level) who have any permission on this collection.
    """
    # 1) Get all PermissionDoc entries for the collection
    perms_cursor = db["permissions"].find(
        {"collection_id": collection_id}
    )
    perms = await perms_cursor.to_list(None)
    if not perms:
        return []

    # 2) Create a mapping of user_email to access_level
    email_to_access_level = {p["user_email"]: p["access_level"] for p in perms}
    user_emails = list(email_to_access_level.keys())

    # 3) Get the user details for those emails
    users_cursor = db["users"].find(
        {"email": {"$in": user_emails}}
    )
    user_details_list = await users_cursor.to_list(None)

    # 4) Convert to UserSummary objects, including access_level
    user_summaries_out: List[UserSummary] = []
    for user_detail in user_details_list:
        email = user_detail["email"]
        if email in email_to_access_level: # Ensure user still has permission
            user_summaries_out.append(UserSummary(
                name=user_detail["name"],
                email=email,
                access_level=email_to_access_level[email]
            ))
    return user_summaries_out


async def get_user_collection_access_level(
    db: AsyncIOMotorDatabase,
    collection_id: str,
    user_email: str
) -> Union[AccessLevel, Literal["none"]]:
    """
    Get the specific access level for a user on a given collection.
    Returns "none" if no explicit permission is found.
    """
    permission_doc = await db["permissions"].find_one({
        "collection_id": collection_id,
        "user_email": user_email
    })

    if permission_doc:
        return permission_doc.get("access_level")
    
    # Before returning "none", check if the user owns the collection.
    # Collection owners implicitly have "control" access.
    collection_doc = await db["collections"].find_one({
        "_id": ObjectId(collection_id), # Assuming collection_id might need conversion to ObjectId
        "user_email": user_email
    })
    if collection_doc:
        return "control"

    return "none"