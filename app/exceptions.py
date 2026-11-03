class UsuarioNaoEncontradoError(Exception):
    def __init__(self, usuario_id: str) -> None:
        super().__init__(f"Usuário não encontrado: {usuario_id}")
        self.usuario_id = usuario_id


class EmailDuplicadoError(Exception):
    def __init__(self, email: str) -> None:
        super().__init__(f"E-mail já cadastrado: {email}")
        self.email = email


class ItemNaoEncontradoError(Exception):
    def __init__(self, item_id: str) -> None:
        super().__init__(f"Item não encontrado: {item_id}")
        self.item_id = item_id


class ItemNaoAutorizadoError(Exception):
    def __init__(self) -> None:
        super().__init__("Ação não permitida para este item")


class TransicaoInvalidaError(Exception):
    def __init__(self, origem: str, destino: str) -> None:
        super().__init__(f"Transição inválida: {origem} -> {destino}")
        self.origem = origem
        self.destino = destino


class ConflitoEstadoError(Exception):
    def __init__(self) -> None:
        super().__init__("Item alterado por outra operação")
