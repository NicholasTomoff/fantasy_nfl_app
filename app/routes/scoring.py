from fastapi import APIRouter, Query
from services.scoring import score_week, project_max_points

router = APIRouter()

# Generate scoring for all users in a league
@router.post("/score/week/{week}/league/{league_id}")
async def trigger_week_scoring(week: int, league_id: int, season: int = Query(...)):
    await score_week(week=week, season=season, league_id=league_id)
    return {
        "status": "success",
        "message": f"Week {week} scored successfully for league {league_id} season {season}"
    }

# Get max possible points for users in a league
@router.get("/league/{league_id}/projected-max-points")
async def get_projected_max_points(league_id: int, currentFinalizedWeek: int = Query(..., description="Most recent fully scored week"), season: int = Query(..., description="Season year")):
    """
    Project maximum possible points for all league members assuming every remaining week
    is a triple-hit (QB+RB+WR) and streaks increment accordingly.
    """
    return await project_max_points(
        league_id=league_id,
        currentFinalizedWeek=currentFinalizedWeek,
        season=season
    )