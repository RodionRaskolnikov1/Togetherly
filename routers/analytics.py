from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Community, CommunityAdmin, Profile, ProfileCommunity, User
from models.education_details import EducationDetails
from models.profession_details import ProfessionDetails
from models.user_logs import UserLogs
from utils.auth_utils import get_current_user
from utils.enums import AccountStatusEnum, ProfileStageEnum


router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_active_users_24h(db: Session) -> int:
    one_day_ago = datetime.now() - timedelta(days=1)
    return db.query(UserLogs.user_id).filter(UserLogs.created_at >= one_day_ago).distinct().count()


def get_recent_activities(db: Session, limit: int = 10) -> list[dict]:
    logs = db.query(UserLogs).order_by(UserLogs.created_at.desc()).limit(limit).all()
    activities = []

    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first()
        first_name = getattr(user, "first_name", "") if user else ""
        last_name = getattr(user, "last_name", "") if user else ""
        full_name = f"{first_name} {last_name}".strip() or "Unknown User"
        activities.append(
            {
                "user_id": log.user_id,
                "user_name": full_name,
                "action": log.action,
                "timestamp": log.created_at.isoformat(),
            }
        )

    return activities


def build_last_twelve_month_keys() -> list[tuple[str, str]]:
    months: list[tuple[str, str]] = []
    current = datetime.now().replace(day=1)

    for offset in range(11, -1, -1):
        year = current.year
        month = current.month - offset
        while month <= 0:
            year -= 1
            month += 12
        month_start = datetime(year, month, 1)
        months.append((month_start.strftime("%Y-%m"), month_start.strftime("%b %Y")))

    return months


@router.get("/dashboard")
def get_dashboard_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_users = db.query(User).count()
    active_users_total = db.query(User).filter(User.account_status == AccountStatusEnum.active).count()
    pending_users = db.query(User).filter(User.account_status == AccountStatusEnum.pending).count()
    active_users_24h = get_active_users_24h(db)
    recent_activities = get_recent_activities(db)

    total_communities = db.query(Community).count()
    communities_with_admin = db.query(Community).join(CommunityAdmin).distinct().count()

    months = build_last_twelve_month_keys()
    first_month_key = months[0][0]
    period_start = datetime.strptime(first_month_key, "%Y-%m")

    users = db.query(User).filter(User.created_at >= period_start).all()

    monthly_registrations: defaultdict[str, int] = defaultdict(int)
    for user in users:
        if user.created_at:
            monthly_registrations[user.created_at.strftime("%Y-%m")] += 1

    registration_trend = [
        {"month": label, "count": monthly_registrations.get(month_key, 0)}
        for month_key, label in months
    ]

    community_growth = [
        {"month": label, "count": total_communities}
        for _, label in months
    ]

    return {
        "user_stats": {
            "total": total_users,
            "active_account": active_users_total,
            "pending": pending_users,
            "active_24h": active_users_24h,
        },
        "community_stats": {
            "total": total_communities,
            "with_admin": communities_with_admin,
        },
        "live_activity": {
            "recent_actions": recent_activities,
        },
        "registration_trend": registration_trend,
        "community_growth": community_growth,
    }


@router.get("/demographics")
def get_demographics_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profiles = db.query(Profile).options(
        joinedload(Profile.user),
        joinedload(Profile.religion),
        joinedload(Profile.caste),
    ).all()

    gender_dist = {"male": 0, "female": 0, "other": 0}
    for profile in profiles:
        if profile.user and profile.user.gender:
            gender_value = profile.user.gender.value if hasattr(profile.user.gender, "value") else str(profile.user.gender)
            gender_key = gender_value.lower()
            if gender_key in gender_dist:
                gender_dist[gender_key] += 1

    age_dist = {"18-24": 0, "25-34": 0, "35-44": 0, "45-54": 0, "55+": 0}
    for profile in profiles:
        if profile.user and profile.user.dob:
            age = (datetime.now().date() - profile.user.dob).days // 365
            if age < 25:
                age_dist["18-24"] += 1
            elif age < 35:
                age_dist["25-34"] += 1
            elif age < 45:
                age_dist["35-44"] += 1
            elif age < 55:
                age_dist["45-54"] += 1
            else:
                age_dist["55+"] += 1

    religion_dist: dict[str, int] = {}
    for profile in profiles:
        if profile.religion and profile.religion.name:
            religion_dist[profile.religion.name] = religion_dist.get(profile.religion.name, 0) + 1

    caste_dist: dict[str, int] = {}
    for profile in profiles:
        if profile.caste and profile.caste.name:
            caste_dist[profile.caste.name] = caste_dist.get(profile.caste.name, 0) + 1
    caste_dist = dict(sorted(caste_dist.items(), key=lambda item: item[1], reverse=True)[:15])

    marital_dist: dict[str, int] = {}
    for profile in profiles:
        if profile.marital_status:
            status_value = profile.marital_status.value if hasattr(profile.marital_status, "value") else str(profile.marital_status)
            status_label = status_value.replace("_", " ").title()
            marital_dist[status_label] = marital_dist.get(status_label, 0) + 1

    return {
        "gender_distribution": gender_dist,
        "age_distribution": age_dist,
        "religion_distribution": religion_dist,
        "caste_distribution": caste_dist,
        "marital_status": marital_dist,
    }


from collections import defaultdict
from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

@router.get("/profiles") # @router.get("/profiles/analytics")
def get_profile_analytics(
    community_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    base_query = db.query(Profile)

    if community_id:
        base_query = (
            base_query.join(ProfileCommunity)
            .filter(ProfileCommunity.community_id == community_id)
            .distinct()
        )

    # -----------------------------
    # Total Profiles
    # -----------------------------
    total_profiles = base_query.count()

    # -----------------------------
    # Stage Counts
    # -----------------------------
    stage_counts = (
        db.query(Profile.profile_stage, func.count(Profile.id))
        .select_from(Profile)
    )

    if community_id:
        stage_counts = (
            stage_counts.join(ProfileCommunity)
            .filter(ProfileCommunity.community_id == community_id)
        )

    stage_counts = stage_counts.group_by(Profile.profile_stage).all()

    stage_dist = {"pending": 0, "approved": 0, "rejected": 0}

    for stage, count in stage_counts:
        stage_dist[stage.value] = count

    verified_profiles = stage_dist.get("approved", 0)
    pending_profiles = stage_dist.get("pending", 0)

    # -----------------------------
    # Education Distribution
    # -----------------------------
    education_query = (
        db.query(EducationDetails.level, func.count(EducationDetails.id))
        .join(Profile)
    )

    if community_id:
        education_query = (
            education_query.join(ProfileCommunity)
            .filter(ProfileCommunity.community_id == community_id)
        )

    education_query = education_query.group_by(EducationDetails.level).all()

    education_dist = {level.value: count for level, count in education_query}

    # -----------------------------
    # Profession Distribution
    # -----------------------------
    profession_query = (
        db.query(ProfessionDetails.organization_name, func.count(Profile.id))
        .join(Profile)
    )

    if community_id:
        profession_query = (
            profession_query.join(ProfileCommunity)
            .filter(ProfileCommunity.community_id == community_id)
        )

    profession_query = (
        profession_query
        .group_by(ProfessionDetails.organization_name)
        .order_by(func.count(Profile.id).desc())
        .limit(15)
        .all()
    )

    profession_dist = {
        org: count for org, count in profession_query if org
    }

    return {
        "total_profiles": total_profiles,
        "verified_profiles": verified_profiles,
        "pending_profiles": pending_profiles,
        "stage_distribution": stage_dist,
        "education_distribution": education_dist,
        "profession_distribution": profession_dist,
    }