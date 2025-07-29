# Deploy do Bot no Railway

## Passo a passo para deploy

1. Faça o fork ou clone deste repositório para seu GitHub.

2. Crie um arquivo chamado `Procfile` na raiz do projeto (já está aqui, mas caso refaça).

3. Confirme que o `main.py` está usando variáveis ambiente `API_TOKEN` e `WEBHOOK_URL`.

4. Faça commit e envie para seu repositório no GitHub.

```bash
git add .
git commit -m "Configuração para deploy Railway"
git push origin main
```

5. Crie uma conta no Railway: https://railway.app/ e conecte seu GitHub.

6. Crie um novo projeto no Railway escolhendo deploy pelo seu repositório GitHub.

7. Configure as variáveis ambiente em Settings > Variables:

| Nome       | Valor                                   |
|------------|----------------------------------------|
| API_TOKEN  | 7920202192:AAEGpjy5k39moDng2DpWqw_LEgmmFU-QI1U  |
| WEBHOOK_URL| https://SEU-APP.up.railway.app/7920202192:AAEGpjy5k39moDng2DpWqw_LEgmmFU-QI1U |

**IMPORTANTE:** Após o deploy, substitua `SEU-APP` pelo domínio gerado para seu app Railway.

8. Clique em Deploy e aguarde o app iniciar.

9. Teste seu bot enviando mensagens no Telegram.

---

## Nota de segurança

Nunca compartilhe seu token publicamente. Depois de configurar e rodar, é recomendado regenerar o token no Telegram.
