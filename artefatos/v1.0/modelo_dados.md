# Modelo de dados da versão 1.0

> Este é o modelo persistido do núcleo de usuários implementado na primeira entrega. A coleção `itens` permanece como modelo-alvo até sua implementação.

## Relacionamento

```text
usuarios 1 ---- N itens
```

O item fica em coleção separada e referencia o proprietário. O endereço é subdocumento apenas do usuário.

## Coleção `usuarios`

```json
{
  "_id": "ObjectId",
  "nome": "Maria da Silva",
  "email": "maria@example.com",
  "senha_hash": "hash scrypt com salt; nunca retornado pela API",
  "tipo": "doador",
  "endereco": {
    "logradouro": "Avenida Brasil",
    "numero": "1200",
    "complemento": "Sala 3",
    "cep": "87000000",
    "cidade": "Maringá"
  },
  "data_adicao": "2026-09-08T12:00:00Z",
  "data_modificacao": "2026-09-08T12:00:00Z"
}
```

## Coleção `itens`

```json
{
  "_id": "ObjectId",
  "titulo": "Notebook Dell usado",
  "descricao": "Funcionando, mas com bateria fraca",
  "categoria": "notebook",
  "marca": "Dell",
  "modelo": "Inspiron 15",
  "condicao": "funcional_com_defeito",
  "destino": "doacao",
  "status": "disponivel",
  "proprietario_id": "ObjectId de usuarios",
  "valor": null,
  "data_adicao": "2026-09-08T12:00:00Z",
  "data_modificacao": "2026-09-08T12:00:00Z"
}
```

## Dicionário resumido

| Estrutura | Papel |
|---|---|
| `usuarios.endereco` | subdocumento lido e atualizado junto com o usuário |
| `usuarios.senha_hash` | hash com salt; campo privado e nunca retornado |
| `itens.proprietario_id` | referência para `usuarios._id` |
| `data_adicao` | instante UTC de criação, imutável |
| `data_modificacao` | instante UTC da última alteração |
| `itens.valor` | campo condicional ao destino `revenda` |

## Decisões

- item não é subdocumento: fica em `itens`, conforme a decisão de escopo da v1.0;
- endereço é subdocumento porque pertence ao usuário e não precisa de ciclo de vida independente;
- item não duplica o endereço do proprietário;
- `historico` e `especificacoes` aninhados entram na v2.0;
- interesses, pontos de coleta e notificações entram na v2.0.

## Índices mínimos

```text
usuarios.email             UNIQUE
itens.proprietario_id      índice para consultas por proprietário
itens.status               índice para catálogo
itens.destino              índice para filtros
```

## Sessão de acesso

A sessão da v1.0 não cria documento MongoDB. Ela permanece somente na memória da API:

```text
identificador aleatório da sessão -> usuario_id, tipo, ultimo_acesso, expiracao
```

O navegador recebe somente o identificador em cookie HttpOnly e não consegue acessá-lo por JavaScript. Reiniciar a API encerra todas as sessões. Nem senha, nem hash, nem identificador de sessão são incluídos nas respostas de usuário.
