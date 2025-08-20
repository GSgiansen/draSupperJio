import os
import telebot
import uvicorn
from fastapi import FastAPI

from ..bot import bot
from ..config import settings

app = FastAPI()


@app.get("/")
def read_root() -> dict[str, str]:
    return {"Hello": "World"}


@app.post(f"/{settings.secret_token}/")
async def process_webhook(update: dict[str, object]) -> None:
    """
    Process webhook calls
    """
    if update:
        update = telebot.types.Update.de_json(update)
        await bot.process_new_updates([update])
    else:
        return


def main() -> None:
    # Get port from environment variable (for Railway/Heroku)
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(
        "tgbot.infrastructure.api:app",
        host="0.0.0.0",  # noqa: S104
        port=port,
        reload=False,  # Disable reload in production
    )


if __name__ == "__main__":
    main()
