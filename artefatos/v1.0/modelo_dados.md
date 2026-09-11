# Modelo de dados da versão 1.0

> Este é o modelo persistido do núcleo de usuários e itens implementado na primeira entrega. Os fluxos de interesse, coleta e histórico continuam reservados para a v2.0.

## Relacionamento

```text
usuarios 1 ---- N itens
```

O item fica em coleção separada e referencia o proprietário por `proprietario_id`. Na v1.0, os campos de endereço ficam no nível raiz do documento de `usuarios`; não existe o subdocumento MongoDB `usuarios.endereco`.

O contrato HTTP também usa os cinco campos no nível raiz da entrada e da resposta. Não existe a chave `endereco` no contrato, no modelo de domínio ou no documento MongoDB da v1.0.

## Coleção `usuarios`

```json
{
  "_id": "ObjectId",
  "nome": "Maria da Silva",
  "email": "maria@example.com",
  "senha_hash": "hash scrypt com salt; nunca retornado pela API",
  "tipo": "doador",
  "logradouro": "Avenida Brasil",
  "numero": "1200",
  "complemento": "Sala 3",
  "cep": "87000000",
  "cidade": "Maringá",
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
  "categoria": "informatica",
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
| `usuarios.logradouro` | campo plano obrigatório do endereço |
| `usuarios.numero` | campo plano obrigatório do endereço, armazenado como texto |
| `usuarios.complemento` | campo plano opcional; pode ser `null` |
| `usuarios.cep` | campo plano com oito dígitos |
| `usuarios.cidade` | campo plano obrigatório usado também no resumo público |
| `usuarios.senha_hash` | hash com salt; campo privado e nunca retornado |
| `itens.proprietario_id` | referência para `usuarios._id` |
| `data_adicao` | instante UTC de criação, imutável |
| `data_modificacao` | instante UTC da última alteração |
| `itens.valor` | campo condicional ao destino `revenda` |

Categorias canônicas de `itens.categoria`: `informatica`, `notebook`, `desktop`, `telefonia`, `celular`, `tablet`, `televisao`, `audio`, `eletrodomestico`, `perifericos`, `monitor`, `impressora` e `outro`. A entrada pode usar maiúsculas, acentos, espaços ou hífen; a API normaliza para minúsculas sem acentos e com `_`.

## Decisões

- item não é subdocumento: fica em `itens`, conforme a decisão de escopo da v1.0;
- campos de endereço são planos em `usuarios`, simplificando a consulta e evitando aninhamento no documento persistido;
- não existe agrupamento `endereco`; os campos são transportados e persistidos diretamente no nível raiz;
- item não duplica os campos de endereço do proprietário;
- `historico` e `especificacoes` aninhados entram na v2.0;
- interesses, pontos de coleta e notificações entram na v2.0.

## Índices mínimos

```text
usuarios.email             UNIQUE
itens.proprietario_id      índice para consultas por proprietário
itens.status               índice para catálogo
itens.destino              índice para filtros
itens.categoria            índice para filtros
itens.condicao             índice para filtros
```

## Sessão de acesso

A sessão da v1.0 não cria documento MongoDB. Ela permanece somente na memória da API:

```text
identificador aleatório da sessão -> usuario_id, tipo, ultimo_acesso, expiracao
```

O navegador recebe somente o identificador em cookie HttpOnly e não consegue acessá-lo por JavaScript. Reiniciar a API encerra todas as sessões. Nem senha, nem hash, nem identificador de sessão são incluídos nas respostas de usuário.
