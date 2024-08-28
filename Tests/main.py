from datetime import datetime, time, timedelta
from uuid import UUID
from typing import Optional, Literal
from enum import Enum
from fastapi import (FastAPI,
                     Query,
                     Path,
                     Body,
                     Cookie,
                     Header)
from pydantic import (BaseModel,
                      Field,
                      HttpUrl,
                      EmailStr)


app1 = FastAPI()
app2 = FastAPI()


'''
    Part 1: Path & Query Parameters
'''

@app1.get('/get/', description="This is our first route.")
async def root():
    return {"message": "hello world"}

@app1.post('/', deprecated=True)
async def post():
    return {"message": "hello from the post route"}

@app1.put('/')
async def put():
    return {"message": "hello from the put route"}

@app1.get('/users')
async def list_users():
    return {"message": "list users route"}

@app1.get('/users/me')
async def show_users_info():
    return {"user_info": "This is the current user"}

@app1.get('/users/{user_id}')
async def get_user(user_id: int):
    return {"user_id": user_id}


class FoodEnum(str, Enum):
    fruits = "fruits"
    vegetables = "vegetables"
    dairy = "dairy"


@app1.get("/foods/{food_name}")
async def get_food(food_name: FoodEnum):
    if food_name == FoodEnum.vegetables:

        return {"food_name": food_name, "message": "You are healthy!"}
    elif food_name.value == "fruits":

        return {"food_name": food_name, "message": "You are fruity!"}
    else:

        return {"food_name": food_name, "message": "You are milky!"}

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

@app1.get("/items")
async def list_items(skip: int = 0, limit: int = 10):
    return fake_items_db[skip: skip+limit]

@app1.get("/items/{item_id}")
async def get_item(item_id: str, q: str | None = None, short: bool = False):
    item = {"item_id": item_id}
    if short:
        item.update({"q": q})
    
    return item


class Image(BaseModel):
    url: HttpUrl
    name: str


# only if you are using python above 3.10 you are able to use float | None = None
class Item(BaseModel):
    name: str = Field(..., example="Foo")
    description: Optional[str] = Field(None, example="A very nice item.")
    price: float = Field(..., example=16.25)
    tax: float | None = Field(None, example=1.67)
    tags: list[str] = Field(..., example=["Atomic Bomb", "13", "2.092349"])
    images: list[Image] | None = Field(None, example=[
                    {
                        "url": "https://pinterest.com/FJfdHfdh.jpg",
                        "name": "Apple Juice"
                    },
                    {
                        "url": "https://www.google.com/images/pic9.jpg",
                        "name": "Banana Milkshake"
                    }
    ])

    # class Config:
    #     json_schema_extra = {
    #         "example": {
    #             "name": "Foo",
    #             "description": "A very nice item.",
    #             "price": 16.25,
    #             "tax": 1.67,
    #             "tags": ["Atomic Bomb", "13", "2.092349"],
    #             "images": [
    #                 {
    #                     "url": "https://pinterest.com/FJfdHfdh.jpg",
    #                     "name": "Apple Juice"
    #                 },
    #                 {
    #                     "url": "https://www.google.com/images/pic9.jpg",
    #                     "name": "Banana Milkshake"
    #                 }
    #             ]
    #         }
    #     }


class Offer(BaseModel):
    name: str
    description: str | None = None
    price: float
    items: list[Item] | None = None


@app1.post('/items')
async def create_item(item: Item) -> dict:
    item_dict = item.model_dump()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({'price_with_tax': price_with_tax})

    return item_dict

@app1.put('/items/{item_id}')
async def create_item_with_put(item_id: int, item: Item, q: str | None = None):
    result = {'item_id': item_id, **item.model_dump()}
    if q:
        result.update({'q': q})

    return result

# if you replace 'fixedquery' parameter with ... in Query(), the q query parameter becomes mandatory
@app1.put('/items')
async def read_items(
    q: str = Query('fixedquery', min_length=3, max_length=10, regex='^fixedquery$'),
    d: list[str] = Query(['foo', 'bar'], deprecated=True, alias='item-query'),
    s: str = Query('None', min_length=4, title='sample query string', description='forgotten')
                            ):
    results = {'items': [{'item_name': 'Foo'}, {'item_name': 'Bar'}]}
    if q:
        results.update({'q': q})
    if d:
        results.update({'d': d})
    if s:
        results.update({'s': s})

    return results

@app1.get('/items_hidden')
async def hidden_query(hidden_query: str = Query(None, include_in_schema=False)):
    if hidden_query:

        return {'hidden_query': hidden_query}
    
    return {'hidden_query': 'Not found!'}

@app1.get('/items_validation/{item_id}')
async def read_items_validation(
    *, item_id: int = Path(..., title='The ID of the item to get', ge=10, le=100),
    q: str, size: float = Query(..., gt=0, le=9.75)
                                        ):
    results = {'item_id': item_id, 'size': size}
    if q:
        results.update({'q': q})
    
    return results

'''
    Part 2: Multiple Parameters
'''


class User(BaseModel):
    username: str
    full_name: str | None = None
    height: int


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None


class UserIn(UserBase):
    password: str


class UserOut(UserBase):
    pass


class Book(BaseModel):
    name: str
    description: str | None = Field(None, title='The description of the book', max_length=300)
    price: float = Field(..., gt=0, description='The price must be greater than zero.')
    tax: float | None = None


class Itemm(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float = 10.5
    tags: list[str] = []


items = {
    "foo": {"name": "Foo", "price": 50.2},
    "bar": {
        "name": "Bar",
        "description": "The bartenders",
        "price": 62,
        "tax": 20.2
    },
    "baz": {
        "name": "Baz",
        "description": None,
        "price": 50.2,
        "tax": 10.5,
        "tags": []
    }
}

@app2.post('/create_user')
async def create_user(
    user: User = Body(..., example={
        "username": "AmirhsFar",
        "full_name": "Amirhossein Farahani",
        "height": 184
        })
                            ):
    return user

@app2.post('/post_user/{user_id}')
async def post_user(
    user_id: int,
    user: User = Body(..., openapi_examples={
        "normal": {
            "summary": "A normal correct example",
            "description": "This *is* a __normal__ example **that** raises _no_ errors",
            "value": {
                "username": "AmirhsFar",
                "full_name": "Amirhossein Farahani",
                "height": 184
            }
        },
        "converted": {
            "summary": "An example with converted data",
            "description": "FastAPI can convert `string` type height to an `integer` one",
            "value": {
                "username": "AmirhsFar",
                "full_name": "Amirhossein Farahani",
                "height": "184"
            }
        },
        "invalid": {
            "summary": "Invalid data is rejected with an error",
            "description": "This example will raise type errors",
            "value": {
                "username": 123,
                "full_name": "Amirhossein Farahani",
                "height": "One Eighty Four"
            }
        }
    })
                            ):
    return {"user_id": user_id, "user": user}

# In the case you have -item- as your only query parameter, embed=True forces you to input {'item': {}}
@app2.put('/items/{item_id}')
async def update_item(
    *, item_id: int = Path(..., title='The ID of the item to get', ge=0, le=150),
    q: str | None = None, item: Item = Body(..., embed=True), user: User,
    importance: int = Body(...)
):
    results = {'item_id': item_id}
    if q:
        results.update({'q': q})
    if item:
        results.update({'item': item})
    if user:
        results.update({'user': user})
    if importance:
        results.update({'importance': importance})

    return results

@app2.put('/books/{book_id}')
async def update_book(book_id: int, book: Book = Body(..., embed=True)):
    results = {'book_id': book_id, 'book': book}

    return results

@app2.put('/item/{item_id}')
async def update_an_item(item_id: int, item: Item):
    results = {'item_id': item_id, 'item': item}

    return results

@app2.post('/offers')
async def create_offer(offer: Offer = Body(..., embed=True)):
    return offer

@app2.post('/images/multiple')
async def create_multiple_images(images: list[Image] = Body(..., embed=True)):
    return images

@app2.post('/blahs')
async def create_some_blahs(blahs: dict[int, float]):
    return blahs

@app2.put('/users/{user_id}')
async def read_users(
    user_id: UUID,
    start_date: datetime = Body(None),
    end_date: datetime = Body(None),
    repeat_at: time = Body(None),
    process_after: timedelta = Body(None)
                            ):
    start_process = start_date + process_after
    duration = end_date - start_process

    return {
        "item_id": user_id,
        "start_date": start_date,
        "end_date": end_date,
        "repeat_at": repeat_at,
        "process_after": process_after,
        "start_process": start_process,
        "duration": duration
        }

@app2.get('/items')
async def read_items(
    cookie_id: str | None = Cookie(None),
    accept_encoding: str | None = Header(None),
    sec_ch_ua: str | None = Header(None),
    user_agent: str | None = Header(None),
    x_token: list[str] | None = Header(None)
                            ):
    return {
        'Cookie_id': cookie_id,
        'Accept-Encoding': accept_encoding,
        'sec-ch-ua': sec_ch_ua,
        'user_agent': user_agent,
        'X-Token values': x_token
        }

@app2.post('/user', response_model=UserOut)
async def create_user(user: UserIn):
    return user

@app2.get(
        '/itemms/{item_id}',
        response_model=Itemm,
        response_model_exclude_unset=True
        )
async def read_item(item_id: Literal["foo", "bar", "baz"]):
    return items[item_id]

@app2.get(
        '/itemms/{item_id}/name',
        response_model=Itemm,
        response_model_include={"name", "description"}
        )
async def read_item_name(item_id: Literal["foo", "bar", "baz"]):
    return items[item_id]

@app2.get(
        '/itemms/{item_id}/public',
        response_model=Itemm,
        response_model_exclude={"tax"}
        )
async def read_item_public_data(item_id: Literal["foo", "bar", "baz"]):
    return items[item_id]
