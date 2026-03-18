L1:# Plano de Implementação — Projeção DRE FOPM Brasil
L2:
L3:## Contexto
L4:
L5:Este documento especifica com precisão o que deve ser implementado no arquivo `fopm.py` para projetar a DRE da BU FOPM Brasil de 2026 a 2030, replicando linha a linha a lógica da planilha `S3_PLANILHA_FUNCIONAL_DE_MODELAGEM_FINANCEIRA.xlsx`, aba `DRE FOPM BRASIL`.
L6:
L7:O input é um CSV histórico com dados de 2018 a 2025. O output é um DataFrame e um CSV com a DRE projetada de 2026 a 2030.
L8:
L9:---
L10:
L11:## Arquivos envolvidos
L12:
L13:```
L14:projecao_bus/
L15:├── fopm.py                      ← motor de projeção (já existe, será editado)
L16:├── dre_fopm_historico.csv       ← histórico 2018–2025 (já existe)
L17:└── projecoes/
L18:    └── projecao_fopm_brasil.csv ← gerado pela execução
L19:```
L20:
L21:---
L22:
L23:## Estrutura do CSV de entrada
L24:
L25:O arquivo `dre_fopm_historico.csv` tem a seguinte estrutura:
L26:
L27:- Uma **linha por métrica**, não por ano
L28:- Coluna `linha`: nome da métrica (igual ao label da planilha)
L29:- Colunas `2018` a `2025`: valores numéricos em R$
L30:- Células vazias onde o dado não existia no histórico
L31:
L32:O `fopm.py` precisa **pivotar** esse formato para uma estrutura com uma linha por ano antes de calcular os ratios. A função `carregar_historico()` já existente espera o formato transposto (uma linha por ano × BU). O primeiro passo da implementação é escrever a função de leitura e pivot específica para esse CSV.
L33:
L34:### Métricas presentes no CSV e seus usos
L35:
L36:| Label no CSV | Uso no motor |
L37:|---|---|
L38:| `FATURAMENTO BRUTO` | validação; não é input direto |
L39:| `RECEITA LÍQUIDA` | base para cálculo de ratios |
L40:| `INCENTIVOS DE PROSPECÇÃO E VENDAS` | numerador do ratio `incentivo_pct_rl` |
L41:| `GASTOS COM PESSOAL` | numerador do ratio `custo_por_func` (÷ n_funcionarios) |
L42:| `OUTRAS DESPESAS DIRETAS` | numerador do ratio `outras_dir_pct_rl` |
L43:| `MARGEM CONTRIBUIÇÃO I` | validação; denominador do ratio `rem_socios_pct_mc1` |
L44:| `REMUNERAÇÃO DIRETA DOS SÓCIOS` | numerador do ratio `rem_socios_pct_mc1` |
L45:| `OUTRAS DESPESAS ADMINISTRATIVAS` | numerador do ratio `outras_adm_pct_rl` |
L46:| `RATEIO ADMINISTRATIVO` | referência histórica; projeção vem de input externo |
L47:| `HONORÁRIOS ADM SÓCIOS DIRETORES` | base da cascata de honorários |
L48:| `EBITDA` | validação do resultado final |
L49:| `# Funcionários - Média` | denominador do ratio `custo_por_func`; input das cascatas |
L50:
L51:**Métricas que NÃO entram nos ratios:**
L52:`AH FB`, `AH RL`, `% s/FB`, `% Margem s/RL`, `PIS/Cofins`, `CSLL`, `IR`, `ISS`, `RECLASSIFICAÇÃO`, sub-linhas de custos (10, 13a, 13b, 13c, 14–24), `EBIT`, `LAIR`, `IRPJ/CSLL`, `LUCRO LÍQUIDO` — todas zeradas ou não projetadas separadamente.
L53:
L54:---
L55:
L56:## Premissas globais (constantes no código)
L57:
L58:### Inflação Focus por ano
L59:
L60:| Ano | Taxa |
L61:|-----|------|
L62:| 2026 | 3,97% |
L63:| 2027 | 3,80% |
L64:| 2028 | 3,50% |
L65:| 2029 | 3,50% |
L66:| 2030 | 3,50% |
L67:
L68:### Alíquota de impostos sobre venda (ISV)
L69:
L70:Fixa em **17,43%** sobre o Faturamento Bruto, composta por:
L71:
L72:| Tributo | Alíquota |
L73:|---------|----------|
L74:| PIS/Cofins | 3,65% |
L75:| CSLL | 2,88% |
L76:| IR | 8,00% |
L77:| ISS | 2,90% |
L78:| **Total** | **17,43%** |
L79:
L80:Constante em todos os anos de projeção.
L81:
L82:### Reajuste real de pessoal
L83:
L84:**+1% ao ano** sobre a inflação. Aplicado em cascata sobre o custo/func.
L85:
L86:### IRPJ/CSLL
L87:
L88:**0%** — regime Lucro Presumido. Alíquota zerada na planilha para toda a projeção.
L89:---
L90:
L91:## Premissas operacionais — inputs manuais por ano
L92:
L93:### Headcount planejado
L94:
L95:| Ano | N.º Funcionários |
L96:|-----|-----------------|
L97:| 2026 | 46 |
L98:| 2027 | 47 |
L99:| 2028 | 48 |
L100:| 2029 | 49 |
L101:| 2030 | 51 |
L102:
L103:### Ociosidade
L104:
L105:| Ano | Ociosidade |
L106:|-----|-----------|
L107:| 2026 | 24,5% |
L108:| 2027 | 24,0% |
L109:| 2028 | 23,0% |
L110:| 2029 | 22,5% |
L111:| 2030 | 21,0% |
L112:
L113:---
L114:
L115:## Ratios históricos — como calcular
L116:
L117:Todos os ratios são **médias aritméticas simples** dos anos 2023, 2024 e 2025. Divisão por zero (RL ou MC I = 0 em algum ano) deve ser tratada substituindo o valor pelo NaN antes de calcular a média.
L118:
L119:### Valores de referência (calculados da planilha)
L120:
L121:| Ratio | 2023 | 2024 | 2025 | **Média (driver)** |
L122:|-------|------|------|------|-------------------|
L123:| Incentivos / RL | 3,452% | 2,467% | 2,636% | **2,852%** |
L124:| Outras Desp. Dir. / RL | 3,266% | 3,817% | 3,051% | **3,378%** |
L125:| Rem. Sócios / MC I | 16,634% | 17,284% | 15,756% | **16,558%** |
L126:| Outras Desp. ADM / RL | 9,255% | 12,742% | 16,318% | **12,772%** |
L127:| Custo/Func (R$/ano) | 154.932 | 130.047 | 150.016 | **144.998** |
L128:| Horas por NF | 314,03 h | 244,69 h | 262,17 h | **273,629 h** |
L129:
L130:O ratio `Horas por NF` é calculado como `Horas Alocadas / Total NFs` para cada ano do período-base, e depois feita a média. Os valores de `Horas Alocadas` e `Total NFs` dos anos históricos vêm da seção PREMISSAS da aba (não da DRE principal).
L131:---
L132:
L133:## Lógica de projeção — linha a linha
L134:
L135:### Pré-cálculo: cascatas iniciais
L136:
L137:Antes do loop de anos, definir os valores de base para as três cascatas:
L138:
L139:**Ticket Médio base:**
L140:```
L141:ticket_base_2026 = (ticket_2024 + ticket_2025) / 2
L142:                 = (95.237 + 91.514) / 2
L143:                 = 93.375,50
L144:```
L145:Este valor é usado **diretamente** como ticket de 2026, sem aplicar inflação. A inflação só entra a partir de 2027.
L146:
L147:**Custo/Func base:**
L148:```
L149:custo_func_base = média(custo_func_2023, custo_func_2024, custo_func_2025)
L150:                = média(154.932, 130.047, 150.016)
L151:                = 144.998
L152:```
L153:Este é o `custo_func_ant` que entra no primeiro ciclo do loop (2026).
L154:
L155:**Honorários base:**
L156:```
L157:honorarios_base = 528.000  (valor de 2024 e 2025, congelado como ponto de partida)
L158:```
L159:
L160:---
L161:
L162:### Loop por ano (executar em sequência: 2026, 2027, 2028, 2029, 2030)
L163:
L164:#### 1. Total Horas
L165:
L166:```
L167:Total Horas = N.º Funcionários × 160 × 12
L168:```
L169:
L170:Fixo: 160 h/mês, 12 meses/ano.
L171:
L172:#### 2. Horas Alocadas
L173:
L174:```
L175:Horas Alocadas = Total Horas × (1 − Ociosidade)
L176:```
L177:
L178:Exemplo 2026: `46 × 160 × 12 × (1 − 0,245) = 66.681,6 h`
L179:
L180:#### 3. Total NFs
L181:
L182:```
L183:Total NFs = Horas Alocadas / Horas por NF
L184:```
L185:
L186:Horas por NF = 273,629 h (constante, calculada no pré-cálculo).
L187:
L188:Exemplo 2026: `66.681,6 / 273,629 = 243,69 NFs`
L189:
L190:#### 4. Ticket Médio (cascata)
L191:
L192:```
L193:2026: ticket = 93.375,50          ← média direta, sem inflação
L194:2027: ticket = ticket_2026 × 1,038
L195:2028: ticket = ticket_2027 × 1,035
L196:2029: ticket = ticket_2028 × 1,035
L197:2030: ticket = ticket_2029 × 1,035
L198:```
L199:
L200:Ao final de cada ano, `ticket_ant = ticket` para o próximo ciclo.
L201:
L202:#### 5. Faturamento Bruto
L203:
L204:```
L205:FB = Total NFs × Ticket Médio
L206:```
L207:
L208:Valores de referência:
L209:
L210:| Ano | FB |
L211:|-----|----|
L212:| 2026 | 22.755.017 |
L213:| 2027 | 24.293.002 |
L214:| 2028 | 26.016.091 |
L215:| 2029 | 27.666.117 |
L216:| 2030 | 30.380.019 |
L217:
L218:#### 6. Impostos sobre Venda
L219:
L220:```
L221:ISV = FB × 0,1743
L222:```
L223:
L224:#### 7. Receita Líquida
L225:
L226:```
L227:RL = FB − ISV
L228:```
L229:
L230:Valores de referência:
L231:
L232:| Ano | RL |
L233:|-----|----|
L234:| 2026 | 18.788.817 |
L235:| 2027 | 20.058.731 |
L236:| 2028 | 21.481.486 |
L237:| 2029 | 22.843.913 |
L238:| 2030 | 25.084.782 |
L239:
L240:#### 8. Reclassificação de Receitas e Despesas
L241:
L242:```
L243:Reclassificação = 0  (zerada em todas as projeções)
L244:```
L245:
L246:#### 9. Incentivos de Prospecção e Vendas
L247:
L248:```
L249:Incentivos = RL × 0,02852
L250:```
L251:
L252:Sub-linhas (Sócios e Equipe) não são projetadas separadamente.
L253:
L254:| Ano | Incentivos |
L255:|-----|-----------|
L256:| 2026 | 535.754 |
L257:
L258:#### 10. Gastos com Pessoal (cascata)
L259:
L260:```
L261:Custo/Func(t) = Custo/Func(t−1) × (1 + inflação(t) + 0,01)
L262:Gastos Pessoal = N.º Funcionários × Custo/Func(t)
L263:```
L264:
L265:Exemplo 2026:
L266:```
L267:Custo/Func_2026 = 144.998 × (1 + 0,0397 + 0,01) = 152.205
L268:Gastos Pessoal_2026 = 46 × 152.205 = 7.001.418
L269:```
L270:
L271:Ao final de cada ano, `custo_func_ant = custo_func` para o próximo ciclo.
L272:
L273:Valores de referência:
L274:
L275:| Ano | Custo/Func | Gastos Pessoal |
L276:|-----|-----------|---------------|
L277:| 2026 | 152.205 | 7.001.418 |
L278:| 2027 | 159.511 | 7.496.996 |
L279:| 2028 | 166.689 | 8.001.050 |
L280:| 2029 | 174.190 | 8.535.287 |
L281:| 2030 | 182.028 | 9.283.431 |
L282:
L283:#### 11. Outras Despesas Diretas
L284:
L285:```
L286:Outras Dir. = RL × 0,03378
L287:```
L288:
L289:Sub-linhas (10 Entradas Operacionais, 13a, 13b, 13c) não são projetadas separadamente.
L290:
L291:| Ano | Outras Dir. |
L292:|-----|------------|
L293:| 2026 | 634.680 |
L294:
L295:#### 12. Margem Contribuição I
L296:
L297:```
L298:MC I = RL − Incentivos − Gastos com Pessoal − Outras Desp. Diretas
L299:```
L300:
L301:Valores de referência:
L302:
L303:| Ano | MC I |
L304:|-----|------|
L305:| 2026 | 10.616.965 |
L306:| 2027 | 11.312.192 |
L307:| 2028 | 12.142.264 |
L308:| 2029 | 12.885.583 |
L309:| 2030 | 14.238.715 |
L310:
L311:#### 13. Remuneração Direta dos Sócios
L312:
L313:```
L314:Rem. Sócios = MC I × 0,16558
L315:```
L316:
L317:| Ano | Rem. Sócios |
L318:|-----|------------|
L319:| 2026 | 1.757.955 |
L320:
L321:#### 14. Margem Contribuição II
L322:
L323:```
L324:MC II = MC I − Remuneração Direta dos Sócios
L325:```
L326:
L327:Valores de referência:
L328:
L329:| Ano | MC II |
L330:|-----|-------|
L331:| 2026 | 8.859.009 |
L332:| 2027 | 9.439.121 |
L333:| 2028 | 10.131.750 |
L334:| 2029 | 10.751.990 |
L335:| 2030 | 11.881.070 |
L336:
L337:#### 15. Outras Despesas Administrativas
L338:
L339:```
L340:Outras ADM = RL × 0,12772
L341:```
L342:
L343:Sub-linhas (Pessoal Não Alocado, 14 Gastos Pessoal, 15 Tecnologia, 16 Eventos, 17 Marketing, 18 Consultorias, 19 Infraestrutura, 20 Outros, 22 Impostos, 24 Impostos Retidos) não são projetadas separadamente.
L344:
L345:| Ano | Outras ADM |
L346:|-----|-----------|
L347:| 2026 | 2.399.701 |
L348:
L349:#### 16. Rateio Administrativo
L350:
L351:```
L352:Rateio ADM = input externo por ano
L353:```
L354:
L355:Vem da aba `DRE ADMINISTRATIVA`: `Total Desp. ADM × (N.Func FOPM / Total N.Func todas as BUs)`. Na fase atual, usar os valores já calculados na planilha como constantes.
L356:
L357:| Ano | Rateio ADM |
L358:|-----|-----------|
L359:| 2026 | 2.231.383 |
L360:| 2027 | 2.260.328 |
L361:| 2028 | 2.304.801 |
L362:| 2029 | 2.295.843 |
L363:| 2030 | 2.370.778 |
L364:
L365:#### 17. Honorários ADM Sócios Diretores (cascata)
L366:
L367:```
L368:Honorários(t) = Honorários(t−1) × (1 + inflação(t))
L369:```
L370:
L371:Base: R$ 528.000 (valor de 2024 e 2025).
L372:
L373:Ao final de cada ano, `honorarios_ant = honorarios` para o próximo ciclo.
L374:
L375:| Ano | Honorários |
L376:|-----|-----------|
L377:| 2026 | 548.962 |
L378:| 2027 | 569.822 |
L379:| 2028 | 589.766 |
L380:| 2029 | 610.408 |
L381:| 2030 | 631.772 |
L382:
L383:**Nota:** A linha `HONORÁRIOS ADM SÓCIOS DIRETORES (Rateio)` não é projetada para a FOPM Brasil — o rateio de honorários é absorvido integralmente pela ADM.
L384:
L385:#### 18. EBITDA
L386:
L387:```
L388:EBITDA = MC II − Outras Desp. ADM − Rateio ADM − Honorários ADM
L389:```
L390:
L391:Valores de referência (gabarito de validação):
L392:
L393:| Ano | EBITDA |
L394:|-----|--------|
L395:| 2026 | 3.678.964 |
L396:| 2027 | 4.047.078 |
L397:| 2028 | 4.493.576 |
L398:| 2029 | 4.928.123 |
L399:| 2030 | 5.674.701 |
L400:
L401:#### 19. Depreciação / Amortização
L402:
L403:```
L404:D&A = 0  (zerada na FOPM — contabilizada na CONS. FORMATO PARCEIRO)
L405:```
L406:
L407:#### 20. EBIT
L408:
L409:```
L410:EBIT = EBITDA − D&A = EBITDA
L411:```
L412:
L413:#### 21. Receita Financeira
L414:
L415:```
L416:Receita Financeira = 0  (tratada na CONS. FORMATO PARCEIRO)
L417:```
L418:
L419:#### 22. Despesa Financeira
L420:
L421:```
L422:Despesa Financeira = 0  (tratada na CONS. FORMATO PARCEIRO)
L423:```
L424:
L425:#### 23. LAIR
L426:
L427:```
L428:LAIR = EBIT + Receita Financeira − Despesa Financeira = EBIT
L429:```
L430:
L431:#### 24. IRPJ / CSLL
L432:
L433:```
L434:IRPJ/CSLL = 0  (alíquota = 0%, regime Lucro Presumido)
L435:```
L436:
L437:#### 25. Lucro Líquido
L438:
L439:```
L440:Lucro Líquido = LAIR − IRPJ/CSLL = LAIR
L441:```
L442:
L443:Igual ao EBITDA para todos os anos de projeção.
L444:
L445:---
L446:
L447:## Output esperado
L448:
L449:A função deve retornar um DataFrame com uma linha por ano e as seguintes colunas, nesta ordem:
L450:
L451:```
L452:bu, ano, n_funcionarios, ociosidade, inflacao_focus,
L453:total_horas, horas_alocadas, horas_por_nf, total_nfs,
L454:ticket_medio, custo_por_func,
L455:faturamento_bruto, impostos_sv, receita_liquida,
L456:incentivos, gastos_pessoal, outras_desp_diretas,
L457:mc1, mc1_pct_rl,
L458:remuneracao_socios,
L459:mc2, mc2_pct_rl,
L460:outras_desp_adm, rateio_adm, honorarios_adm,
L461:ebitda, ebitda_pct_rl,
L462:ebit, lair, irpj_csll, lucro_liquido
L463:```
L464:
L465:O CSV de saída é gravado em `projecoes/projecao_fopm_brasil.csv`.
L466:
L467:---
L468:
L469:## Validação
L470:
L471:Após a execução, comparar os valores calculados com o gabarito abaixo. Tolerância: diferença absoluta < R$ 1,00 por célula.
L472:
L473:| Linha | 2026 | 2027 | 2028 | 2029 | 2030 |
L474:|-------|------|------|------|------|------|
L475:| Faturamento Bruto | 22.755.017 | 24.293.002 | 26.016.091 | 27.666.117 | 30.380.019 |
L476:| Receita Líquida | 18.788.817 | 20.058.731 | 21.481.486 | 22.843.913 | 25.084.782 |
L477:| Gastos com Pessoal | 7.001.418 | 7.496.996 | 8.001.050 | 8.535.287 | 9.283.431 |
L478:| MC I | 10.616.965 | 11.312.192 | 12.142.264 | 12.885.583 | 14.238.715 |
L479:| MC II | 8.859.009 | 9.439.121 | 10.131.750 | 10.751.990 | 11.881.070 |
L480:| EBITDA | 3.678.964 | 4.047.078 | 4.493.576 | 4.928.123 | 5.674.701 |
L481:| Lucro Líquido | 3.678.964 | 4.047.078 | 4.493.576 | 4.928.123 | 5.674.701 |
L482:
L483:### Diagnóstico de desvios
L484:
L485:Se o FB bater mas a RL divergir → alíquota ISV incorreta (deve ser exatamente 17,43%).
L486:
L487:Se a RL bater mas o MC I divergir → checar qual dos três ratios está errado: incentivos (2,852%), outras dir. (3,378%) ou gastos pessoal (cascata custo/func).
L488:
L489:Se o MC I bater mas o MC II divergir → ratio rem. sócios incorreto (deve ser 16,558% × MC I).
L490:
L491:Se o MC II bater mas o EBITDA divergir → checar outras ADM (12,772% × RL), rateio (valores fixos acima) ou honorários (cascata sobre 528.000).
L492:
L493:Se ticket 2026 sair ~95.147 em vez de ~93.376 → o código está aplicando inflação sobre o ticket 2025 em vez de usar a média 2024+2025 diretamente.
L494:
L495:---
L496:
L497:## Armadilhas conhecidas
L498:
L499:**Ticket Médio 2026 não usa inflação.** O valor de 2026 é a média aritmética dos tickets de 2024 e 2025, usado diretamente — sem multiplicar por `(1 + inflação)`. A inflação só entra a partir de 2027 em cascata sobre o valor anterior.
L500:
L501:**Custo/Func é calculado sobre a média dos três anos-base, não sobre o último ano.** A média de 2023, 2024 e 2025 é R$ 144.998, não R$ 150.016 (que seria só o valor de 2025).
L502:
L503:**O rateio ADM é input externo.** Não é calculado dentro da função da FOPM. Na fase atual, usar os cinco valores fixos listados acima. Quando o orquestrador multi-BU for implementado, esse input passará a ser calculado dinamicamente.
L504:
L505:**Honorários crescem por cascata, não são fixos.** O valor de R$ 528.000 é a base de partida; a partir de 2026 aplica-se a inflação sobre o valor do ano anterior.
L506:
L507:**As sub-linhas de custo não são projetadas.** Dentro de Outras Despesas Diretas, Outras Despesas ADM e Incentivos existem itens detalhados (linhas 10, 13a, 13b, 14–24) que aparecem no histórico mas são zerados ou absorvidos pelo ratio agregado nas projeções. O motor não os calcula individualmente.

