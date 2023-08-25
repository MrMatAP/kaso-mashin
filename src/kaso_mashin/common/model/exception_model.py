import pydantic


class ExceptionSchema(pydantic.BaseModel):
    """
    Schema for an exception
    """
    status: int = pydantic.Field(description='The exception status code', default=500)
    msg: str = pydantic.Field(description='A user-readable error description')

    model_config = {
        'json_schema_extra': {
            'examples': [
                {
                    'status': 400,
                    'msg': 'I did not like your input, at all'
                }
            ]
        }
    }
