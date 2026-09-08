class UsuarioNaoEncontradoError(Exception):
    def __init__(self, usuario_id: str) -> None:
        super().__init__(f"Usuário não encontrado: {usuario_id}")
        self.usuario_id = usuario_id
