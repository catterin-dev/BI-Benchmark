
import strawberry
from strawberry.fastapi import GraphQLRouter
from fastapi import FastAPI
from src.db import summary as get_summary


@strawberry.type
class CategorySummary:
    category: str
    count: int
    average_amount: float


@strawberry.type
class BISummary:
    total_events: int
    total_amount: float
    by_category: list[CategorySummary]


@strawberry.type
class Query:

    @strawberry.field
    def summary(self) -> BISummary:
        d = get_summary()

        return BISummary(
            total_events=d["total_events"],
            total_amount=d["total_amount"],
            by_category=[
                CategorySummary(**x)
                for x in d["by_category"]
            ]
        )


schema = strawberry.Schema(query=Query)

app = FastAPI(
    title="BI Benchmark GraphQL",
    version="1.0.0"
)

app.include_router(
    GraphQLRouter(schema),
    prefix="/graphql"
)

