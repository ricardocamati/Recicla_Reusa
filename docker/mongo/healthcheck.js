// A imagem oficial cria o administrador antes de iniciar o replica set.
// Não inicializar durante o processo temporário de criação desse usuário.
const admin = db.getSiblingDB("admin");
const autenticado = admin.auth(
  process.env.MONGO_INITDB_ROOT_USERNAME,
  process.env.MONGO_INITDB_ROOT_PASSWORD,
);
if (!autenticado) quit(1);
const opcoes = admin.runCommand({ getCmdLineOpts: 1 });
const replicacao = opcoes.parsed?.replication;
if (!replicacao?.replSet && !replicacao?.replSetName) quit(1);
try {
  rs.status();
} catch (erro) {
  if (erro.code === 94 || erro.codeName === "NotYetInitialized") {
    rs.initiate({ _id: "rs0", members: [{ _id: 0, host: "mongo:27017" }] });
  } else {
    quit(1);
  }
}
quit(admin.runCommand({ hello: 1 }).isWritablePrimary ? 0 : 1);
