# Instruções para Reiniciar o Sistema de Trading

## Passos para Reinicialização

1. **Pare o sistema de trading atual**
   - Certifique-se de que todas as ordens pendentes sejam canceladas
   - Salve qualquer posição aberta em um arquivo temporário se necessário

2. **Atualize o código**
   - Substitua o arquivo `src/trade_execution/binance_client.py` com a versão corrigida
   - Verifique se não há erros de sintaxe no novo arquivo:
     ```bash
     python -m py_compile src/trade_execution/binance_client.py
     ```

3. **Reinicie o sistema de trading**
   - Execute o comando de inicialização do sistema (ex: `python main.py` ou similar)
   - Verifique se o sistema inicia sem erros

4. **Monitore os logs**
   - Observe os logs do sistema para verificar se há erros LOT_SIZE ou NOTIONAL
   - Procure por mensagens de sucesso na execução de ordens

5. **Teste com trades reais no testnet da Binance**
   - Antes de usar em produção, execute alguns trades de teste na Binance Testnet
   - Verifique se os trades são executados com sucesso e se as quantidades estão corretas

6. **Verificação Final**
   - Confirme que os trades estão sendo executados sem erros
   - Verifique se os valores notionais das ordens estão dentro dos limites mínimos da Binance

## Troubleshooting

Se ainda ocorrerem erros:

1. **Verifique as dependências**
   - Certifique-se de que todas as dependências estão instaladas corretamente:
     ```bash
     pip install -r requirements.txt
     ```

2. **Verifique a conectividade com a Binance**
   - Confirme que as chaves da API estão configuradas corretamente
   - Verifique se há conectividade com a API da Binance

3. **Consulte os logs detalhados**
   - Analise os logs completos para identificar possíveis problemas
   - Procure por mensagens de erro específicas

## Contato

Se os problemas persistirem, entre em contato com o time de desenvolvimento para assistência adicional.