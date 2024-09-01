from datetime import datetime, time, timedelta
from uuid import UUID
from typing import Optional, Literal, Union
from enum import Enum
from fastapi import (FastAPI,
                     Query,
                     Path,
                     Body,
                     Cookie,
                     Header,
                     Form,
                     File,
                     Depends,
                     exception_handlers,
                     responses,
                     UploadFile,
                     status,
                     HTTPException,
                     Request,
                     exceptions,
                     encoders)
from pydantic import (BaseModel,
                      Field,
                      HttpUrl,
                      EmailStr)


app1 = FastAPI()
app2 = FastAPI()
app3 = FastAPI()
app4 = FastAPI()
app5 = FastAPI()


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
async def create_item_with_put(
    item_id: int,
    item: Item,
    q: str | None = None
    ):
    result = {'item_id': item_id, **item.model_dump()}
    if q:
        result.update({'q': q})

    return result

# if you replace 'fixedquery' parameter with ... in Query(),
# the q query parameter becomes mandatory
@app1.put('/items')
async def read_items(
    q: str = Query(
        'fixedquery',
        min_length=3,
        max_length=10,
        regex='^fixedquery$'
        ),
    d: list[str] = Query(
        ['foo', 'bar'],
        deprecated=True,
        alias='item-query'
        ),
    s: str = Query(
        'None',
        min_length=4,
        title='sample query string',
        description='forgotten'
        )
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
    Part 2: Multiple Parameters & Response Body
'''


class User(BaseModel):
    username: str
    full_name: str | None = None
    height: int


class UserLogin(BaseModel):
    username: str
    password: str


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None


class UserIn(UserBase):
    password: str


class UserInDB(UserBase):
    hashed_password: str


class UserOut(UserBase):
    pass


class Book(BaseModel):
    name: str
    description: str | None = Field(
        None,
        title='The description of the book',
        max_length=300
        )
    price: float = Field(
        ...,
        gt=0,
        description='The price must be greater than zero.'
        )
    tax: float | None = None


class Itemm(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float = 10.5
    tags: list[str] = []


class BaseItem(BaseModel):
    description: str
    type: str


class CarItem(BaseItem):
    type: str = 'car'


class PlaneItem(BaseItem):
    type: str = 'plane'
    size: int


class ListItem(BaseModel):
    name: str
    description: str


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

itemms = {
    'item1': {
        'description': 'All my friends drive a low rider',
        'type': 'car'
    },
    'item2': {
        'description': 'Music is my aeroplane',
        'type': 'plane',
        'size': 5
    }
}

list_items = [
    {"name": "Foo", "description": "There comes my hero"},
    {"name": "Red", "description": "It's my aeroplane"}
]

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
            "description": """This *is* a __normal__ 
                                example **that** raises _no_ errors""",
            "value": {
                "username": "AmirhsFar",
                "full_name": "Amirhossein Farahani",
                "height": 184
            }
        },
        "converted": {
            "summary": "An example with converted data",
            "description": """FastAPI can convert `string`
                                    type height to an `integer` one""",
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

# In the case you have -item- as your only query parameter,
# embed=True forces you to input {'item': {}}
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


'''
    Part 3: Models, Status Codes and Request Files
'''

def fake_password_hasher(raw_password: str):
    return f"supersecret{raw_password}"

def fake_save_user(user_in: UserIn):
    hashed_password = fake_password_hasher(user_in.password)
    user_in_db = UserInDB(**user_in.model_dump(), hashed_password=hashed_password)
    print("User 'saved'.")

    return user_in_db

@app3.post("/user/", response_model=UserOut)
async def create_user(user_in: UserIn):
    user_saved = fake_save_user(user_in)

    return user_saved

@app3.get('/items/{item_id}', response_model=Union[PlaneItem, CarItem])
async def read_item(item_id: Literal['item1', 'item2']):
    return itemms[item_id]

@app3.post('/items', status_code=status.HTTP_201_CREATED)
async def create_item(name: str):
    return {'name': name}

@app3.delete('/item/{pk}', status_code=204)
async def delete_item(pk: str):
    print('pk', pk)

    return pk

@app3.get('/items', status_code=301)
async def read_items_redirect():
    return {"hello": "world"}

@app3.post('/login_no_form')
async def login_without_using_form(user: UserLogin):
    return user

@app3.post('/login_form')
async def login_with_using_form(
    username: str = Form(...),
    password: str = Form(...)
    ):
    print('password:', password)

    return {'username': username}

@app3.post('/files')
async def create_file(files: list[bytes] = File(
                                        NotImplementedError,
                                        description='A file read as bytes'
                                    )):
    if not files:

        return {'message': 'No files sent'}

    return {'files_sizes': [len(file) for file in files]}

@app3.post('/uploadfile')
async def create_upload_file(file: UploadFile = File(
                                        None,
                                        description='A file read as upload file'
                                    )):
    if not file:

        return {'message': 'No upload file sent'}

    return {'filename': file.filename}

@app3.post('/uploadfiles')
async def create_upload_file(files: list[UploadFile] = File(
                                        None,
                                        description='Files read as upload file'
                                    )):
    if not files:

        return {'message': 'No upload files sent'}

    return {'filenames': [file.filename for file in files]}

@app3.get('/')
async def main():
    content = '''
                <body>
                <form action="/files" enctype="multipart/form-data" method="post">
                <input name="files" type="file" multiple>
                <input type="submit">
                </form>
                <form action="/uploadfiles" enctype="multipart/form-data" method="post">
                <input name="files" type="file" multiple>
                <input type="submit">
                </form>
                </body>
            '''
    
    return responses.HTMLResponse(content=content)

@app3.post('/filess')
async def create_file(
    file: bytes = File(...),
    fileb: UploadFile = File(...),
    token: str = Form(...),
    hello: str = Body(...)
    ):
    return {
        "file_size": len(file),
        "token": token,
        "fileb_content_type": fileb.content_type,
        "hello": hello
    }


'''
    Part 4: Error Handling, APIs' Documentation, JSON Encoder & Dependencies (Intro)
'''


class Tags(Enum):
    items = 'items'
    users = 'users'
    instances = 'instances'


class Ittem(BaseModel):
    title: str
    size: int


class Instance(BaseModel):
    name: str
    description: str | None = None
    price: float | None = None
    tax: float = 10.5
    tags: list[str] = []


class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name


instances = {
    'Foo': {
        'name': "Foo",
        'price': 50.2
    },
    'Bar': {
        'name': "Bar",
        'description': "The bartenders",
        'price': 62,
        'tax': 20.2
    },
    'Baz': {
        'name': "Baz",
        'description': None,
        'price': 59.2,
        'tax': 10.5,
        'tags': []
    }
}

ittems = {"foo": "The Foo Wrestlers"}

@app4.get('/items/{item_id}')
async def read_item(item_id: str):
    if item_id not in ittems:
        raise HTTPException(
            status_code=404,
            detail="Item not found",
            headers={"X-Error": "There goes my error"}
        )
    
    return {"item": ittems[item_id]}

@app4.exception_handler(UnicornException)
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    return responses.JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something."}
    )

@app4.get("/unicorns/{name}")
async def read_unicorns(name: str):
    if name == "Yolo":
        raise UnicornException(name=name)
    
    return {"unicorn_name": name}

'''
@app4.exception_handler(exceptions.RequestValidationError)
async def validation_exception_handler(request, exc):
    return responses.PlainTextResponse(str(exc), status_code=400)
'''

'''
@app4.exception_handler(exceptions.RequestValidationError)
async def validation_exception_handler(request: Request, exc: exceptions.RequestValidationError):
    return responses.JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=encoders.jsonable_encoder({"detail": exc.errors(), "body": exc.body})
    )
'''

'''
@app4.exception_handler(exceptions.StarletteHTTPException)
async def http_exception_handler(request, exc):
    return responses.PlainTextResponse(str(exc.detail), status_code=exc.status_code)
'''

@app4.exception_handler(exceptions.StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    print(f"OMG! An HTTP error!: {repr(exc)}")

    return await exception_handlers.http_exception_handler(request, exc)

@app4.exception_handler(exceptions.RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"OMG! The client sent invalid data!: {exc}")

    return await exception_handlers.request_validation_exception_handler(request, exc)

@app4.get('/validation_items/{item_id}')
async def read_validation_items(item_id: int):
    if item_id == 3:
        raise HTTPException(status_code=418, detail="Nope! I don't like 3!")
    
    return {"item_id": item_id}

@app4.get('/blah_items/{item_id}')
async def read_items(item_id: int):
    if item_id == 3:
        raise HTTPException(
            status_code=418,
            detail="Nope! I don't like 3"
        )
    
    return {'item_id': item_id}

@app4.post(
        '/items',
        response_model=Item,
        status_code=status.HTTP_201_CREATED,
        tags=[Tags.items],
        summary='Create an Item',
        response_description='The created item'
        # description='''Create an Item with all the information: 
        #                     name, description, price, tax, and a set of tags'''
    )
async def create_item(item: Item):
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: required
    - **tax**: if the item doesn't have tax, you can omit this
    - **tags**: a set of unique tag strings for this item
    """
    return item

@app4.get('/items', tags=[Tags.items], deprecated=True)
async def read_items():
    return [{'name': 'Foo', 'price': 42}]

@app4.get('/users', tags=[Tags.users])
async def read_users():
    return [{'username': 'PhoebeBuffay'}]

@app4.put('/instances/{instance_id}', tags=[Tags.instances])
def update_instance(instance_id: str, instance: Instance):
    update_instance_encoded = encoders.jsonable_encoder(instance)
    instances[instance_id] = update_instance_encoded

    return update_instance_encoded

@app4.get(
        '/instances/{instance_id}',
        response_model=Instance,
        tags=[Tags.instances]
    )
async def read_instance(instance_id: str):
    return instances.get(instance_id)

@app4.patch(
        '/instances/{instance_id}',
        response_model=Instance,
        tags=[Tags.instances]
    )
def patch_instance(instance_id: str, instance: Instance):
    stored_instance_data = instances.get(instance_id)
    if stored_instance_data is not None:
        stored_instance_model = Instance(**stored_instance_data)
    else:
        stored_instance_model = Instance(name=instance_id)
    update_data = instance.model_dump(exclude_unset=True)
    print(update_data)
    updated_instance = stored_instance_model.model_copy(update=update_data)
    instances[instance_id] = encoders.jsonable_encoder(updated_instance)
    print(instances[instance_id])

    return updated_instance

async def hello():
    return 'world'

async def common_paramteres(
        q: str | None = None,
        skip: int = 0,
        limit: int = 100,
        blah: str = Depends(hello)
    ):
    return {'q': q, 'skip': skip, 'limit': limit, 'hello': blah}

@app4.get('/books')
async def read_books(commons: dict = Depends(common_paramteres)):
    return commons

@app4.get('/ussers')
async def read_ussers(commons: dict = Depends(common_paramteres)):
    return commons


'''
    Part 5: Dependencies
'''


class CommonQueryParams:
    def __init__(
            self,
            instance_id: int,
            q: str | None = None,
            skip: int = 0,
            limit: int = 100
        ):
        self.instance_id = instance_id
        self.q = q
        self.skip = skip
        self.limit = limit


fake_instances_db = [
    {'instance_name': 'Foo'},
    {'instance_name': 'Bar'},
    {'instance_name': 'Baz'}
]

@app5.get('/instances/{instance_id}')
async def read_items(commons: CommonQueryParams=Depends()):
    response = {}
    response.update({'instance_id': commons.instance_id})
    if commons.q:
        response.update({'q': commons.q})
    instances = fake_instances_db[commons.skip: commons.skip+commons.limit]
    response.update({'instances': instances})

    return response

def query_extractor(q: str | None = None):
    return q

def query_or_body_extractor(
        q: str = Depends(query_extractor),
        last_query: str | None = Body(None)
    ):
    if q:

        return q

    return last_query
    
@app5.post('/item')
async def try_query(query_or_body: str = Depends(query_or_body_extractor)):
    return {'q_or_body': query_or_body}

async def verify_token(x_token: str = Header(...)):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

async def verify_key(x_key: str = Header(...)):
    if x_key != 'fake-super-secret-key':
        raise HTTPException(status_code=400, detail='X-key header invalid')

    return x_key

dependency_app = FastAPI(dependencies=[Depends(verify_token), Depends(verify_key)])

@dependency_app.get('/items')
async def read_items():
    return [{'item': 'Foo'}, {'item': 'Bar'}]

@dependency_app.get('/users')
async def read_users():
    return [{'username': 'Rick'}, {'username': 'Morty'}]
