import pathlib


class Renderable:
    """
    Base class for renderable entities
    """

    def render_to(self, path: pathlib.Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, mode='w', encoding='UTF-8') as p:
            p.write(self.render())

    def render(self) -> str:
        return ''
