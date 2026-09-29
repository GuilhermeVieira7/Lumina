# Segurança no Lumina

Resumo do que protege os dados das crianças e das famílias, para consulta na defesa do TCC.
Cada item aponta onde está no código e qual teste confere o comportamento.

## 1. Senhas guardadas com Argon2id

- A senha nunca é guardada. O banco guarda só um *hash* Argon2id, por exemplo:
  `$argon2id$v=19$m=65536,t=3,p=4$<sal>$<hash>`.
- **Por que Argon2id:** venceu a *Password Hashing Competition* (2015) e é o primeiro recomendado
  pela OWASP. Ele é "caro em memória": cada tentativa usa 64 MiB, o que torna muito lento
  testar milhões de senhas numa placa de vídeo, ao contrário de MD5 ou SHA-256.
- **Parâmetros:** `m=65536` (64 MiB de memória), `t=3` (3 passadas), `p=4` (4 linhas em paralelo).
  O **sal aleatório** faz duas pessoas com a mesma senha terem hashes diferentes.
- **Migração sem perder contas:** contas criadas antes, em bcrypt, continuam entrando. No primeiro
  login certo, a senha é regravada em Argon2id sem o usuário perceber.
- **Mesmo tempo com ou sem usuário:** quando o usuário não existe, o login calcula um hash
  de mentira. Assim ninguém descobre quais nomes de usuário existem medindo o tempo de resposta.
- Código: `backend/auth.py` (`hash_password`, `verify_password`, `needs_rehash`).
  Testes: `tests/test_security.py`.

**Para mostrar na banca:** no pgAdmin, abra a tabela `users` e veja que a coluna `password_hash`
só tem textos `$argon2id$...`, nunca a senha.

## 2. Limite de tentativas

- Depois de **8 senhas erradas em 5 minutos**, o sistema recusa novas tentativas por alguns minutos
  (HTTP 429). A senha certa zera a contagem.
- **Onde vale:** no login, na senha do Painel dos Adultos e na exclusão de conta.
- Código: `backend/rate_limit.py`. Teste: `test_too_many_wrong_passwords_are_blocked`.

## 3. Login com token (JWT)

- Depois do login, o navegador recebe um token assinado (HS256) com validade de 24 horas.
- A chave que assina vem do `.env` (`SECRET_KEY`). Sem ela, o servidor cria uma chave aleatória
  a cada início, nunca uma chave fixa conhecida.
- Código: `backend/auth.py` (`create_access_token`, `get_current_user`).

## 4. Quem vê os dados de cada criança

- **Responsável:** só o responsável que cadastrou a criança vê e edita os dados dela.
- **Profissional (terapeuta, escola):** só vê os dados depois que o responsável convida e o
  profissional aceita. O responsável pode revogar o acesso a qualquer momento.
- **Pedido sem permissão:** qualquer pedido a uma criança sem permissão responde "não encontrado" (404),
  sem revelar que ela existe.
- **Painel dos Adultos:** pede a senha da conta de novo. Assim a criança, usando o mesmo aparelho,
  não entra no painel.
- Código: `backend/permissions.py`. Testes: `test_professional_access_invite_accept_revoke`,
  `test_summary_is_private`, `test_moods_are_private_and_deleted_with_the_child`.

## 5. LGPD: dados de crianças

- **Consentimento:** o cadastro só é aceito com o termo de consentimento, e a data do aceite
  fica registrada.
- **Dados mínimos:** não há campo de diagnóstico. O sistema guarda só o necessário para o
  acompanhamento.
- **Exclusão:** "Excluir conta" apaga a conta e todos os dados das crianças cadastradas, em cascata,
  depois de confirmar a senha.
- **Foto opcional:** a foto da criança é reduzida no próprio aparelho e validada no servidor
  (tipo real da imagem e tamanho máximo).
- Testes: `test_register_requires_consent`, `test_delete_account_removes_children_data`,
  `tests/test_profile_photo.py`.

## 6. Servidor e banco

- **Cabeçalhos de segurança:** `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` (impede
  abrir o app dentro de outro site) e `Referrer-Policy: no-referrer`.
- **CORS fechado:** o app é servido pelo mesmo servidor da API, então nenhum outro site pode
  chamar a API pelo navegador.
- **Consultas ao banco:** passam pelo SQLAlchemy com parâmetros, sem montar SQL com texto do
  usuário. Isso protege contra *SQL injection*.
- **Textos na tela:** tudo que o usuário digita é "escapado" antes de aparecer (`UI.esc`), o que
  protege contra *XSS*.
- **Docker:** o PostgreSQL e o pgAdmin só aceitam conexões do próprio computador
  (`127.0.0.1`). Todas as senhas e chaves ficam no `.env`, que não vai para o Git.

## 7. Limites conhecidos (para responder com honestidade)

- **HTTPS:** para uso real na internet, é preciso colocar o app atrás de HTTPS (por exemplo,
  Azure App Service ou um proxy com certificado). Em `localhost`, isso não se aplica.
- **Limite de tentativas em memória:** vale para um servidor só. Com vários servidores, o
  contador precisaria ir para um banco compartilhado (Redis, por exemplo).
- **Token no navegador:** o token fica no `localStorage`. Uma evolução seria cookie `HttpOnly`
  com proteção CSRF.
