from sanic import Sanic
from sanic.response import json

import os

app = Sanic("stackquiz")


@app.route("/random")
async def get_random_question(request):
    # TODO: icons, logos, fetching things...
    return json(
        {
            "question_id": None,
            "text": None,
            "answers": [{"name": None, "apiname": None}],
        }
    )


@app.route("/answer")
async def answer_question(request):
    # input: question ID, answer
    return json({"correct_answer": None})


if __name__ == "__main__":
    app.run(host=os.environ["STACKQUIZ_HOST"], port=int(os.environ["STACKQUIZ_PORT"]))
