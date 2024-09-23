from datetime import datetime, time, timedelta
import time as Time
from uuid import UUID
from typing import Optional, Literal, Union
from enum import Enum
from jose import jwt, JWTError
from passlib import context
from fastapi.middleware.cors import CORSMiddleware
from starlette import middleware as Middleware
from fastapi import (FastAPI,
                     Query,
                     Path,
                     Body,
                     Cookie,
                     Header,
                     Form,
                     File,
                     Depends,
                     staticfiles,
                     security,
                     BackgroundTasks,
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
app6 = FastAPI()


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
        pattern='^fixedquery$'
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


class SecurityUser(UserBase):
    disabled: bool | None = None


class SecurityUserInDB(SecurityUser):
    hashed_password: str


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
        response_description='The created item',
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
    Part 5: Dependencies, Security (OAuth2 & JWT), Middleware & CORS
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


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class TokenUser(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool = False


class TokenUserInDB(TokenUser):
    hashed_password: str


class MyMiddleware(Middleware.base.BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = Time.time()
        response = await call_next(request)
        process_time = Time.time() - start_time
        response.headers['X-Process-Time'] = str(process_time)

        return response


fake_users_db = {
    'johndoe': dict(
        username='johndoe',
        full_name='John Doe',
        email='johndoe@example.com',
        hashed_password='$2b$12$gjdIFl0Y5Ee5TSx0zlgoau2VD3Oec2pBAZNbES4POuQ.JgFMIOYGe',
        disabled=False
    ),
    'alice': dict(
        username='alice',
        full_name='Alice Wonderson',
        email='alice@example.com',
        hashed_password='fakehashedsecret2',
        disabled=True
    )
}

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

oauth2_scheme = security.OAuth2PasswordBearer(tokenUrl='token')

def fake_hash_password(password: str):
    return f'fakehashed{password}'

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]

        return SecurityUserInDB(**user_dict)

def fake_decode_token(token):
    return get_user(fake_users_db, token)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid authentication credentials',
            headers={'WWW-Authenticate': 'Bearer'}
        )

    return user

async def get_current_active_user(current_user: SecurityUser = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail='Inactive user')
    
    return current_user

'''
@app5.post('/token')
async def login(form_data: security.OAuth2PasswordRequestForm = Depends()):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password"
        )
    user = SecurityUserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password"
        )
    
    return {'access_token': user.username, 'token_type': 'bearer'}
'''

@app5.get('/token')
async def read_token(token: str = Depends(oauth2_scheme)):
    return {'token': token}

@app5.get('/users/me')
async def get_me(current_user: SecurityUser = Depends(get_current_active_user)):
    return current_user

SECRET_KEY = 'thequickbrownfoxjumpsoverthelazydog'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = context.CryptContext(schemes=['bcrypt'], deprecated='auto')

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]

        return TokenUserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:

        return False
    
    if not verify_password(password, user.hashed_password):

        return False
    
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({'exp':expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

@app5.post('/token', response_model=Token)
async def login_for_access_token(form_data: security.OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': user.username},
        expires_delta=access_token_expires
    )

    return {'access_token': access_token, 'token_type': 'bearer'}

async def get_current_user_jwt(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW_Authenticate': 'Bearer'}
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user_jwt(current_user: TokenUser = Depends(get_current_user_jwt)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail='Inactive user')
    
    return current_user

@app5.get('/users/me/jwt', response_model=TokenUser)
async def get_me(current_user: TokenUser = Depends(get_current_active_user_jwt)):
    return current_user

@app5.get('/users/me/items')
async def read_own_items(current_user: TokenUser = Depends(get_current_active_user_jwt)):
    return [{'item_id': 'Foo', 'owner': current_user.username}]

origins = [
    '*'
]
app5.add_middleware(MyMiddleware)
app5.add_middleware(CORSMiddleware, allow_origins=origins)

@app5.get('/blah')
async def blah():
    return {'hello': 'world'}


'''
    Part 6: Background Tasks, Metadata, Docs URLs, Static Files & Testing
'''


class TestItem(BaseModel):
    id: str
    title:str
    description: str | None = None


def write_notification(email: str, message=''):
    with open('log.txt', mode='w') as email_file:
        content = f"notification for {email}: {message}\n"
        Time.sleep(5)
        email_file.write(content)

@app6.post('/send-notification/{email}')
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(
        write_notification, email, message='some notification'
    )

    return {'message': 'Notification sent in the background'}

def write_log(message: str):
    with open('log.txt', mode='a') as log:
        log.write(message)

def get_query(background_tasks: BackgroundTasks, q: str | None = None):
    if q:
        message = f"found query: {q}\n"
        background_tasks.add_task(write_log, message)
    
    return q

@app6.post('/send-notifications/{email}')
async def send_notification(
    email: str,
    background_tasks: BackgroundTasks,
    q: str = Depends(get_query)
):
    message = f"message to {email}\n"
    background_tasks.add_task(write_log, message)

    return {'message': 'Message sent', 'query': q}

description = '''
ChimichangApp API helps you do awesome stuff.

## Items

You can **read items**.

## Users

You will be able to:

* **Create users** (_not implemented_).
* **Read users** (_not implemented_).
'''

tags_metadata = [
    dict(
        name='users',
        description='Operations with users, The **login** logic is also here.'
    ),
    dict(
        name='items',
        description='Manage items. So _fancy_ they have their own docs.',
        externalDocs=dict(
            description='Items external docs',
            url='https://www.fastapi.com'
        )
    )
]

desc_app = FastAPI(
    title='ChimichangApp',
    description=description,
    version='0.0.1',
    terms_of_service='http://example.com/terms',
    contact=dict(
        name='Deadpoolio the Amazing',
        url='http://x-force.example.com/contact',
        email='dp@x-force.example.com'
    ),
    license_info=dict(
        name='Apache 2.0',
        url='https://www.apache.org/licenses/LICENSE-2.0.html'
    ),
    openapi_tags=tags_metadata,
    openapi_url='/api/v1/openapi.json',
    docs_url='/documents',
    # redoc_url=None
)

@desc_app.get('/users', tags=['users'])
async def read_users():
    return [dict(name='Harry'), dict(name='Ron')]

@desc_app.get('/items', tags=['items'])
async def read_items():
    return [dict(name='wand'), dict(name='flying broom')]

app6.mount('/static', staticfiles.StaticFiles(directory='static'), name='static')

fake_secret_token = 'coneofsilence'
fake_db = dict(
    foo=dict(
        id='foo',
        title='Foo',
        description='There goes my hero'
    ),
    bar=dict(
        id='bar',
        title='Bar',
        description='The bartenders'
    )
)

@app6.get('/items/{item_id}', response_model=TestItem)
async def read_main(item_id: str, x_token: str = Header(...)):
    if x_token != fake_secret_token:
        raise HTTPException(
            status_code=400,
            detail='Invalid X-Token header'
        )
    item = fake_db.get(item_id)
    if item is None:
        raise HTTPException(
            status_code=404,
            detail='Item not found'
        )
    
    return item

@app6.post('/items', response_model=TestItem)
async def create_item(item: TestItem, x_token: str = Header(...)):
    if x_token != fake_secret_token:
        raise HTTPException(
            status_code=400,
            detail='Invalid X-Token header'
        )
    if item.id in fake_db:
        raise HTTPException(
            status_code=400,
            detail='Item already exists'
        )
    fake_db[item.id] = item

    return item
