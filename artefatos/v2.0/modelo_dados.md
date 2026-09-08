# Modelo de dados da versão 2.0

## Relacionamentos

```text
usuarios 1 ---- N itens
usuarios 1 ---- N interesses
itens    1 ---- N interesses
usuarios 1 ---- N notificacoes
itens    1 ---- N notificacoes
interesses 1 ---- N notificacoes
usuarios 1 ---- N pontos_coleta (responsável)
pontos_coleta 1 ---- N itens de descarte
```

## Coleção `usuarios`

```json
{
  "_id": "ObjectId",
  "nome": "Maria da Silva",
  "email": "maria@example.com",
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
  "ponto_coleta_id": null,
  "valor": null,
  "especificacoes": {
    "processador": "Intel Core i5",
    "memoria_ram": "8 GB",
    "armazenamento": "256 GB SSD"
  },
  "historico": [
    {
      "etapa": "cadastro",
      "status": "disponivel",
      "data_evento": "2026-09-08T12:00:00Z",
      "responsavel_id": "ObjectId de usuarios",
      "observacao": "Item cadastrado para doação"
    }
  ],
  "data_adicao": "2026-09-08T12:00:00Z",
  "data_modificacao": "2026-09-08T12:00:00Z"
}
```

## Coleção `interesses`

```json
{
  "_id": "ObjectId",
  "item_id": "ObjectId de itens",
  "usuario_id": "ObjectId de usuarios",
  "status": "pendente",
  "data_adicao": "2026-09-08T13:00:00Z",
  "data_modificacao": "2026-09-08T13:00:00Z"
}
```

## Coleção `pontos_coleta`

```json
{
  "_id": "ObjectId",
  "nome": "Ponto de Coleta Central",
  "responsavel_id": "ObjectId de usuarios",
  "endereco": {
    "logradouro": "Rua das Flores",
    "numero": "100",
    "complemento": null,
    "cep": "87010000",
    "cidade": "Maringá"
  },
  "categorias_aceitas": ["celular", "notebook", "monitor"],
  "horario_atendimento": "Segunda a sexta, 08:00–17:00",
  "data_adicao": "2026-09-08T12:00:00Z",
  "data_modificacao": "2026-09-08T12:00:00Z"
}
```

## Coleção `notificacoes`

```json
{
  "_id": "ObjectId",
  "usuario_id": "ObjectId do destinatário em usuarios",
  "item_id": "ObjectId de itens",
  "interesse_id": "ObjectId de interesses",
  "tipo": "status_item_alterado",
  "titulo": "Atualização em item de seu interesse",
  "mensagem": "O notebook foi reservado.",
  "evento_id": "identificador único do evento de domínio",
  "lida": false,
  "data_leitura": null,
  "data_adicao": "2026-09-08T14:00:00Z",
  "data_modificacao": "2026-09-08T14:00:00Z"
}
```

## Decisões de modelagem

- endereço é aninhado em usuários e pontos porque pertence integralmente a esses documentos;
- item referencia o proprietário e não copia seu endereço;
- interesses ficam separados porque um item pode receber vários;
- histórico fica dentro do item porque pertence ao seu ciclo de vida;
- especificações são flexíveis para atender categorias diferentes;
- notificações ficam separadas para permitir consulta por destinatário e controle de leitura;
- `evento_id` evita duplicar a mesma notificação para o mesmo destinatário;
- todas as coleções possuem datas de adição e modificação;
- `ponto_coleta_id` e `valor` são condicionais ao destino.
