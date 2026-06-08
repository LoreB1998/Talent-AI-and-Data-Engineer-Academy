---
embed-resources: true
format:
  html:
    code-fold: show
    css: style.css
    number-sections: true
    respect-user-color-scheme: true
    smooth-scroll: true
    theme:
      dark: darkly
      light: flatly
    toc: true
    toc-depth: 3
    toc-title: Indice
lang: it
subtitle: Scikit-Learn --- Algoritmi Principali
title: Guida agli Iperparametri
watch-inputs: true
---

# Come leggere questa guida

Ogni sezione descrive un algoritmo con la tabella degli iperparametri,
le indicazioni per il `GridSearchCV` e i consigli pratici.

La colonna **Impatto** indica quanto l'iperparametro influisce sulle
performance:

- 🔴 **Alto** = ottimizzare sempre.
- 🟠 **Medio** = ottimizzare se hai budget computazionale.
- 🟢 **Basso** = spesso il default è sufficiente.

::: callout-note
## Convenzione pipeline sklearn

Tutti i `param_grid` usano il prefisso `'nome_step__'` per riferirsi
agli iperparametri all'interno di una `Pipeline`. Es: `'clf__C'` per il
parametro `C` di un `SVC` inserito come step `'clf'`.
:::

::: callout-tip
## Regola d'oro: scala logaritmica

Per iperparametri come `C`, `alpha`, `gamma` --- cercare sempre su scala
logaritmica: `[0.001, 0.01, 0.1, 1, 10, 100]`. Una griglia lineare
`[1, 2, 3, 4, 5]` spreca combinazioni nella zona densa.
:::

------------------------------------------------------------------------

# K-Nearest Neighbors --- KNeighborsClassifier/Regressor

## Descrizione

KNN è un algoritmo *lazy*: non costruisce un modello esplicito durante
il training, ma memorizza tutti i dati. In fase di `predict`, cerca i
$k$ campioni più vicini e combina le loro etichette (voto per
classificazione, media per regressione). È estremamente flessibile ma
costoso in predict su dataset grandi.

::: callout-important
## Prerequisito fondamentale

KNN è sensibilissimo alla scala delle feature. Usare sempre
`StandardScaler` o `MinMaxScaler` **PRIMA** di KNN. Senza
normalizzazione, feature con range ampio dominano la distanza.
:::

## Iperparametri

  -------------------------------------------------------------------------------
  Iperparametro     Tipo / Default    Impatto           Descrizione
  ----------------- ----------------- ----------------- -------------------------
  `n_neighbors`     int / `5`         🔴 Alto           Numero di vicini $k$. $k$
                                                        piccolo = alta varianza
                                                        (overfitting), $k$ grande
                                                        = alto bias
                                                        (underfitting). Regola
                                                        pratica: provare
                                                        $k = \sqrt{n_{train}}$.
                                                        Valori dispari per
                                                        classificazione binaria.

  `weights`         str / `'uniform'` 🟠 Medio          `'uniform'`: ogni vicino
                                                        vale uguale.
                                                        `'distance'`: peso
                                                        inversamente
                                                        proporzionale alla
                                                        distanza ($1/d$). Useful
                                                        con $k$ grande o dati a
                                                        densità variabile.

  `metric`          str /             🔴 Alto           Funzione di distanza. Con
                    `'minkowski'`                       $p=2$: euclidea. Con
                                                        $p=1$: Manhattan. Altre:
                                                        `'chebyshev'`, `'cosine'`
                                                        (testo), `'hamming'`
                                                        (binario). La scelta
                                                        cambia radicalmente i
                                                        vicini trovati.

  `p`               int / `2`         🟠 Medio          Esponente Minkowski.
                                                        $p=1$ = Manhattan
                                                        (robusto outlier), $p=2$
                                                        = Euclidea (geometria
                                                        standard). Ignorato se
                                                        `metric` non è
                                                        `'minkowski'`.

  `algorithm`       str / `'auto'`    🟢 Basso          Struttura per ricerca
                                                        vicini. `'auto'` sceglie:
                                                        `'kd_tree'` per dim \<
                                                        20, `'ball_tree'` per dim
                                                        \> 20, `'brute'` como
                                                        fallback. Non influenza
                                                        l'accuracy.

  `leaf_size`       int / `30`        🟢 Basso          Dimensione foglie in
                                                        kd_tree/ball_tree.
                                                        Bilancia memoria e
                                                        velocità di query. Non
                                                        influenza l'accuracy,
                                                        solo le prestazioni.

  `n_jobs`          int / `None`      🟢 Basso          Parallelismo in predict.
                                                        `-1` = usa tutti i core.
                                                        Molto utile su dataset
                                                        grandi.
  -------------------------------------------------------------------------------

## GridSearchCV consigliato

\`\`\`{python} #\| eval: false from sklearn.neighbors import
KNeighborsClassifier from sklearn.model_selection import GridSearchCV

param_grid = { 'knn\_\_n_neighbors': \[1, 3, 5, 7, 11, 15, 21\],
'knn\_\_weights': \['uniform', 'distance'\], 'knn\_\_metric':
\['euclidean', 'manhattan', 'chebyshev'\], 'knn\_\_p': \[1, 2\], \# solo
con metric='minkowski' } \# Combinazioni totali: 7 x 2 x 3 = 42 (+
varianti p)


    ---

    # Support Vector Machine — SVC / SVR

    ## Descrizione

    SVM cerca l'iperpiano che massimizza il margine tra le classi. I *Support Vectors* sono i campioni più vicini all'iperpiano. Con kernel non-lineari (`rbf`, `poly`), mappa i dati in uno spazio di dimensione superiore dove la separazione lineare è possibile.

    ## Iperparametri — SVC

    | Iperparametro | Tipo / Default | Impatto | Descrizione |
    | --- | --- | --- | --- |
    | `C` | float / `1.0` | 🔴 Alto | Regolarizzazione. `C` piccolo = margine ampio, errori tollerati (underfitting). `C` grande = margine stretto, zero errori su train (overfitting). Cercare su scala log: `[0.001, 0.01, 0.1, 1, 10, 100, 1000]`. |
    | `kernel` | str / `'rbf'` | 🔴 Alto | `'linear'`: separazione lineare (veloce, alta dim). `'rbf'`: radiale, very general purpose. `'poly'`: interazioni polinomiali. `'sigmoid'`: simile rete neurale. `'rbf'` è il default affidabile. |
    | `gamma` | str/float / `'scale'` | 🔴 Alto | Raggio di influenza del kernel rbf/poly/sigmoid. `gamma` alto = boundary complesso (overfitting). `gamma` basso = boundary liscio. `'scale'` = $1 / (n_{feat} \cdot Var(X))$, `'auto'` = $1 / n_{feat}$. |
    | `degree` | int / `3` | 🟠 Medio | Grado polinomio per `kernel='poly'`. Grado 2 = boundary quadratico, grado 3 = cubico. Ignorato da rbf/linear. Gradi alti rischiano overfitting. |
    | `coef0` | float / `0.0` | 🟢 Basso | Termine costante per kernel poly e sigmoid. Influenza quanto le feature di alto grado sono rilevanti. Raramente necessario ottimizzare. |
    | `class_weight` | str/dict / `None` | 🟠 Medio | `'balanced'`: pesa le classi inversamente alla frequenza. Fondamentale con dataset sbilanciati. Può essere un dizionario `{0: 1, 1: 10}` per pesi manuali. |
    | `probability` | bool / `False` | Funzionale | Abilita `predict_proba()` tramite calibrazione Platt (5-fold CV interna). Necessario per ROC-AUC. Aumenta il tempo di fit. Le probabilità sono stime, non valori esatti. |
    | `decision_function_shape` | str / `'ovr'` | 🟠 Medio | `'ovr'`: One-vs-Rest (default, più stabile). `'ovo'`: One-vs-One ($K \cdot (K-1) / 2$ classificatori). Con 3 classi: ovr=3 classificatori, ovo=3 classificatori. Con molte classi ovr è più efficiente. |
    | `max_iter` | int / `-1` | 🟢 Basso | Iterazioni massime del solver. `-1` = nessun limite. Aumentare se si riceve `ConvergenceWarning`. |

    ## Iperparametri — SVR (regressione)

    SVR aggiunge l'iperparametro `epsilon` (la banda di tolleranza intorno all'iperpiano):

    | Iperparametro | Tipo / Default | Impatto | Descrizione |
    | --- | --- | --- | --- |
    | `epsilon` | float / `0.1` | 🔴 Alto | Ampiezza della banda epsilon-insensitive. Errori minori di `epsilon` non vengono penalizzati. Valore troppo piccolo = overfitting, troppo grande = underfitting. |
    | `C` | float / `1.0` | 🔴 Alto | Come SVC: regola il tradeoff tra errori di training e ampiezza del margine. |
    | `kernel` | str / `'rbf'` | 🔴 Alto | Identico a SVC. |
    | `gamma` | str/float / `'scale'` | 🔴 Alto | Identico a SVC. |

    ## GridSearchCV consigliato

    ::: {.callout-note}

    ## Nota su Gamma e Degree

    `gamma` e `degree` sono ignorati da `kernel='linear'`. Si consiglia di usare `ParameterGrid` con condizioni o effettuare la ricerca separatamente per kernel.
    :::

    ```{python}
    #| eval: false
    param_grid_svc = {
        'svc__C':       [0.01, 0.1, 1, 10, 100],
        'svc__kernel':  ['linear', 'rbf', 'poly'],
        'svc__gamma':   ['scale', 'auto', 0.01, 0.1, 1],  # solo rbf/poly
        'svc__degree':  [2, 3, 4],                         # solo poly
    }

------------------------------------------------------------------------

# Decision Tree --- DecisionTreeClassifier/Regressor

## Descrizione

Il Decision Tree costruisce una sequenza di regole if-else apprese dai
dati, scegliendo ad ogni nodo lo split che massimizza la riduzione di
impurità (Gini o entropia). Altamente interpretabile ma incline
all'overfitting senza un'adeguata regolarizzazione. È la struttura base
di Random Forest e Gradient Boosting.

## Iperparametri

  ---------------------------------------------------------------------------------------------------
  Iperparametro                Tipo / Default    Impatto           Descrizione
  ---------------------------- ----------------- ----------------- ----------------------------------
  `max_depth`                  int/None / `None` 🔴 Alto           Profondità massima. `None` =
                                                                   cresce finché le foglie sono pure
                                                                   (overfitting garantito).
                                                                   Principale strumento di
                                                                   regolarizzazione. Provare
                                                                   `[3, 5, 7, 10, None]`. Per Iris:
                                                                   depth 3-4 è ottimale.

  `criterion`                  str / `'gini'`    🟠 Medio          `'gini'`: Gini impurity (più
                                                                   veloce). `'entropy'`: information
                                                                   gain. `'log_loss'` da sklearn 1.1.
                                                                   In pratica i risultati sono molto
                                                                   simili. `'gini'` è il default
                                                                   affidabile.

  `min_samples_split`          int/float / `2`   🔴 Alto           Minimo campioni per dividere un
                                                                   nodo interno. Valori $> 2$
                                                                   impediscono split su nodi piccoli.
                                                                   Se float, è una frazione: `0.05` =
                                                                   5% dei campioni.

  `min_samples_leaf`           int/float / `1`   🔴 Alto           Minimo campioni in ogni foglia.
                                                                   Fortemente regolarizzante: elimina
                                                                   foglie con pochi campioni.
                                                                   Preferire a `max_depth` per una
                                                                   regolarizzazione più granulare.

  `max_features`               str/int/None /    🟠 Medio          Feature considerate per ogni
                               `None`                              split. `None`=tutte.
                                                                   `'sqrt'`=radice (standard RF).
                                                                   `'log2'`.
                                                                   int/float=numero/frazione. Ridurlo
                                                                   introduce casualità utile negli
                                                                   ensemble.

  `max_leaf_nodes`             int/None / `None` 🟠 Medio          Numero massimo di foglie.
                                                                   Alternativa a `max_depth`:
                                                                   l'albero cresce *best-first*
                                                                   (riduzione impurità massima) fino
                                                                   al limite.

  `min_weight_fraction_leaf`   float / `0.0`     🟢 Basso          Frazione minima del peso totale in
                                                                   ogni foglia. Usare con
                                                                   `sample_weight` per dataset
                                                                   sbilanciati.

  `ccp_alpha`                  float / `0.0`     🟠 Medio          Cost-Complexity Pruning. Valori
                                                                   $> 0$ potano rami che non
                                                                   migliorano abbastanza l'impurità.
                                                                   Usare
                                                                   `cost_complexity_pruning_path()`
                                                                   per trovare il range ottimale.

  `class_weight`               str/dict / `None` 🟠 Medio          `'balanced'` per classi
                                                                   sbilanciate. Influenza la scelta
                                                                   degli split pesando gli errori
                                                                   sulle classi rare.

  `random_state`               int / `None`      🟢 Basso          Seed per la riproducibilità degli
                                                                   split in caso di tie-breaking.
                                                                   Impostare sempre per esperimenti
                                                                   riproducibili.
  ---------------------------------------------------------------------------------------------------

## GridSearchCV consigliato

::: callout-warning
## Elevato numero di combinazioni

La griglia sottostante genera
$5 \times 2 \times 4 \times 5 \times 3 \times 4 = 2400$ combinazioni
totali. Si raccomanda fortemente l'utilizzo di `RandomizedSearchCV`!
:::

\`\`\`{python} #\| eval: false param_grid_dt = { 'dt\_\_max_depth':
\[None, 3, 5, 7, 10\], 'dt\_\_criterion': \['gini', 'entropy'\],
'dt\_\_min_samples_split': \[2, 5, 10, 20\], 'dt\_\_min_samples_leaf':
\[1, 2, 4, 8, 16\], 'dt\_\_max_features': \[None, 'sqrt', 'log2'\],
'dt\_\_ccp_alpha': \[0.0, 0.001, 0.005, 0.01\], }


    ---

    # Random Forest — RandomForestClassifier/Regressor

    ## Descrizione

    Random Forest addestra $N$ Decision Tree su *bootstrap samples* diversi (bagging), selezionando un sottoinsieme casuale di feature ad ogni split. La predizione finale è determinata dal voto di maggioranza (classificazione) o dalla media (regressione) di tutti gli alberi. La diversificazione degli alberi riduce drasticamente la varianza rispetto al singolo Decision Tree.

    ## Iperparametri

    | Iperparametro | Tipo / Default | Impatto | Descrizione |
    | --- | --- | --- | --- |
    | `n_estimators` | int / `100` | 🔴 Alto | Numero di alberi. Più alberi = migliore generalizzazione, ma con rendimenti decrescenti oltre 100-500. Non causa overfitting aggiungerne di più. Regola: aumentare fino alla stabilizzazione del *OOB error*. |
    | `max_features` | str/int/float / `'sqrt'` | 🔴 Alto | Feature per ogni split. `'sqrt'` (default classif.) = $\sqrt{n_{features}}$. `'log2'`. `1.0` = tutte (disattiva la casualità delle feature). Valori bassi = alberi più diversificati ma singolarmente meno performanti. |
    | `max_depth` | int/None / `None` | 🔴 Alto | Profondità max di ogni albero. `None`=crescita completa (accettabile in RF grazie al bagging). Limitare se la RAM è un problema o con dataset molto grandi. |
    | `min_samples_split` | int/float / `2` | 🟠 Medio | Come Decision Tree. Valori $> 2$ riducono la complessità dei singoli alberi. |
    | `min_samples_leaf` | int/float / `1` | 🟠 Medio | Come Decision Tree. Aumentare per regolarizzare (es. 4-8 su dataset piccoli). |
    | `bootstrap` | bool / `True` | 🟠 Medio | `True` = bootstrap sampling (con rimpiazzo). `False` = usa tutto il dataset per ogni albero (più simile a bagging puro). `True` è il default corretto per RF. |
    | `oob_score` | bool / `False` | 🟢 Basso | `True` = valuta ogni albero sui campioni *Out-of-Bag* (non usati nel suo bootstrap). Offre una stima accurata del validation error senza necessità di CV. |
    | `n_jobs` | int / `None` | 🟢 Basso | Parallelismo. `-1` = usa tutti i core disponibili. Il training di una Random Forest è un processo massivamente parallelo (*embarrassingly parallel*). |
    | `class_weight` | str/dict / `None` | 🟠 Medio | `'balanced'` o `'balanced_subsample'` per classi sbilanciate. `'balanced_subsample'` ricalcola i pesi dinamicamente su ogni bootstrap sample. |
    | `max_samples` | int/float / `None` | 🟠 Medio | Campioni per bootstrap. `None` = `n_samples`. float = frazione del totale. Ridurre per velocizzare il training su dataset enormi. |
    | `random_state` | int / `None` | 🟢 Basso | Seed per la riproducibilità. |

    ## GridSearchCV consigliato

    ```{python}
    #| eval: false
    from sklearn.model_selection import RandomizedSearchCV
    from scipy.stats import randint

    param_dist_rf = {
        'rf__n_estimators':     [100, 200, 500],
        'rf__max_features':     ['sqrt', 'log2', 0.3, 0.5],
        'rf__max_depth':        [None, 5, 10, 20],
        'rf__min_samples_leaf': [1, 2, 4, 8],
        'rf__min_samples_split':[2, 5, 10],
    }
    # Con molti iperparametri preferire RandomizedSearchCV (es. n_iter=50)

------------------------------------------------------------------------

# Gradient Boosting --- GradientBoostingClassifier/Regressor

## Descrizione

Gradient Boosting costruisce gli alberi in modo sequenziale: ogni nuovo
albero viene addestrato per correggere i residui (errori) del
precedente. A differenza di RF (parallelo), GB è sequenziale e
intrinsecamente più lento, ma spesso offre una precisione superiore.

::: callout-tip
## Dataset $> 10.000$ campioni

Per dataset di grandi dimensioni ($> 10.000$ campioni) si raccomanda
l'uso di **HistGradientBoostingClassifier**, la versione ottimizzata
(ispirata a XGBoost/LightGBM). Gestisce i `NaN` nativamente, supporta
l'early stopping interno ed è drasticamente più veloce. I suoi parametri
chiave sono: `max_iter` (=n_estimators), `learning_rate`, `max_depth`,
`l2_regularization`, `max_leaf_nodes`.
:::

## Iperparametri --- GradientBoostingClassifier

  ---------------------------------------------------------------------------------
  Iperparametro           Tipo / Default    Impatto           Descrizione
  ----------------------- ----------------- ----------------- ---------------------
  `n_estimators`          int / `100`       🔴 Alto           Numero di alberi
                                                              (boosting rounds).
                                                              **A differenza di RF,
                                                              un numero eccessivo
                                                              di alberi causa
                                                              overfitting!** Usare
                                                              early stopping o CV
                                                              per identificare il
                                                              valore ottimale.

  `learning_rate`         float / `0.1`     🔴 Alto           Tasso di
                                                              apprendimento: scala
                                                              il contributo di
                                                              ciascun albero. `lr`
                                                              basso = modello più
                                                              generalizzabile ma
                                                              richiede più alberi.
                                                              Tradeoff fondamentale
                                                              con `n_estimators`.

  `max_depth`             int / `3`         🔴 Alto           Profondità alberi. GB
                                                              utilizza per design
                                                              alberi poco profondi
                                                              (*shallow*, 3-5).
                                                              Alberi profondi
                                                              portano a un rapido
                                                              overfitting nel
                                                              boosting sequenziale.

  `subsample`             float / `1.0`     🔴 Alto           Frazione di campioni
                                                              per ogni albero.
                                                              Valori $< 1.0$
                                                              introducono lo
                                                              *Stochastic Gradient
                                                              Boosting* (riduce
                                                              l'overfitting).
                                                              Valore tipico:
                                                              `0.7 - 0.8`.

  `min_samples_split`     int/float / `2`   🟠 Medio          Come Decision Tree.
                                                              Valori $> 2$
                                                              regolarizzano gli
                                                              alberi deboli.

  `min_samples_leaf`      int/float / `1`   🟠 Medio          Come Decision Tree.
                                                              Valori $> 1$ stabili
                                                              su dataset piccoli.

  `max_features`          str/int/None /    🟠 Medio          Come RF: riduce la
                          `None`                              correlazione tra
                                                              alberi successivi.
                                                              `'sqrt'` spesso
                                                              migliora la
                                                              generalizzazione.

  `loss`                  str /             🟠 Medio          Funzione di perdita.
                          `'log_loss'`                        `'log_loss'`
                                                              (cross-entropy) per
                                                              classificazione.
                                                              `'exponential'` =
                                                              AdaBoost. Per
                                                              regressione:
                                                              `'squared_error'`,
                                                              `'absolute_error'`,
                                                              `'huber'`.

  `warm_start`            bool / `False`    🟢 Basso          `True` = permette di
                                                              continuare il
                                                              training dall'ultimo
                                                              fit aggiungendo
                                                              alberi. Utile per
                                                              determinare
                                                              `n_estimators` in
                                                              modo incrementale.

  `validation_fraction`   float / `0.1`     🟢 Basso          Frazione del train
                                                              set da riservare
                                                              all'early stopping.
                                                              Da usare in
                                                              combinazione con
                                                              `n_iter_no_change`.

  `n_iter_no_change`      int/None / `None` 🟠 Medio          Early stopping:
                                                              interrompe
                                                              l'addestramento se lo
                                                              score di validazione
                                                              non migliora per $N$
                                                              iterazioni
                                                              consecutive. Ottimo
                                                              per risparmiare tempo
                                                              ed evitare
                                                              overfitting.
  ---------------------------------------------------------------------------------

## GridSearchCV consigliato

::: callout-note
## Ottimizzazione congiunta

`n_estimators` e `learning_rate` vanno tassativamente ottimizzati
insieme: un `lr` basso richiede un `n_estimators` alto. Una buona
pratica consiste nel confrontare configurazioni polarizzate, ad esempio:
`(n_estimators=500, lr=0.01)` vs `(n_estimators=100, lr=0.1)`.
:::

\`\`\`{python} #\| eval: false param_grid_gb = { 'gb\_\_n_estimators':
\[100, 200, 500\], 'gb\_\_learning_rate': \[0.01, 0.05, 0.1, 0.2\],
'gb\_\_max_depth': \[3, 4, 5\], 'gb\_\_subsample': \[0.7, 0.8, 1.0\],
'gb\_\_max_features': \['sqrt', None\], }


    ---

    # Logistic Regression — LogisticRegression

    ## Descrizione

    A dispetto del nome, si tratta di un classificatore lineare. Modella la probabilità di appartenenza a una classe mediante la funzione sigmoide applicata a una combinazione lineare delle feature. È estremamente veloce, interpretabile e rappresenta un'ottima baseline. Gestisce scenari multiclasse tramite approccio OvR (default) o multinomiale.

    ## Iperparametri

    | Iperparametro | Tipo / Default | Impatto | Descrizione |
    | --- | --- | --- | --- |
    | `C` | float / `1.0` | 🔴 Alto | Inverso della forza di regolarizzazione (come in SVM). `C` grande = meno regolarizzazione (rischio overfitting). `C` piccolo = regolarizzazione forte (rischio underfitting). Griglia tipica: `[0.001, 0.01, 0.1, 1, 10, 100]`. |
    | `penalty` | str / `'l2'` | 🔴 Alto | `'l2'`: Ridge, penalizza $\sum w^2$. `'l1'`: Lasso, impone la sparsità dei coefficienti (feature selection automatica). `'elasticnet'`: combinazione lineare di l1 e l2. `None`: nessuna regolarizzazione. |
    | `solver` | str / `'lbfgs'` | 🟠 Medio | `'lbfgs'`: default, ottimo per dati densi (non supporta l1). `'saga'`: supporta tutte le penalità, ideale per grandi dataset. `'liblinear'`: efficiente su piccoli dataset. `'newton-cg'`: preciso ma lento. |
    | `max_iter` | int / `100` | 🟢 Basso | Iterazioni massime del solver. Aumentare a `500 - 1000` se compare un `ConvergenceWarning`. Con feature scalate correttamente, `100` è spesso sufficiente. |
    | `multi_class` | str / `'auto'` | 🟠 Medio | `'ovr'`: One-vs-Rest ($K$ classificatori binari). `'multinomial'`: cross-entropy calcolata globalmente (più accurato). `'auto'` seleziona in base al solver. |
    | `class_weight` | str/dict / `None` | 🟠 Medio | `'balanced'` per gestire classi sbilanciate. Modifica i pesi direttamente nella loss function. |
    | `l1_ratio` | float / `None` | 🟠 Medio | Richiesto solo con `penalty='elasticnet'`. Bilancia il contributo l1 e l2: `0` = solo l2, `1` = solo l1. Cercare su: `[0.1, 0.3, 0.5, 0.7, 0.9]`. |
    | `tol` | float / `1e-4` | 🟢 Basso | Tolleranza per la convergenza del solver. Ridurre per soluzioni più precise a scapito del tempo di calcolo. |

    ## GridSearchCV consigliato

    ```{python}
    #| eval: false
    param_grid_lr = {
        'lr__C':       [0.001, 0.01, 0.1, 1, 10, 100],
        'lr__penalty': ['l1', 'l2', 'elasticnet', None],
        'lr__solver':  ['saga'],  # 'saga' supporta tutte le combinazioni di penalità
        'lr__l1_ratio':[0.1, 0.5, 0.9],  # attivo solo con elasticnet
    }

------------------------------------------------------------------------

# Naive Bayes

## Descrizione

Famiglia di classificatori basati sul Teorema di Bayes con l'assunzione
"naive" (ingenua) di indipendenza condizionale tra le feature, dato
l'output. Nonostante l'ipotesi semplificativa sia raramente realistica,
l'algoritmo si rivela incredibilmente efficace sulla classificazione di
testi e dati categorici.

## GaussianNB

Utilizzato per feature continue, assumendo che esse seguano una
distribuzione normale (Gaussiana).

  ------------------------------------------------------------------------------------
  Iperparametro     Tipo / Default    Impatto           Descrizione
  ----------------- ----------------- ----------------- ------------------------------
  `var_smoothing`   float / `1e-9`    🔴 Alto           Porzione della varianza
                                                        massima di tutte le feature
                                                        aggiunta alle varianze per
                                                        garantire stabilità numerica
                                                        (evita divisioni per zero).
                                                        Cercare su:
                                                        `[1e-11, 1e-7, 1e-5, 1e-3]`.

  `priors`          array/None /      🟠 Medio          Probabilità a priori delle
                    `None`                              classi. Se `None`, vengono
                                                        stimate direttamente dai dati
                                                        di training.
  ------------------------------------------------------------------------------------

## MultinomialNB

Ideale per conteggi e frequenze discrete (es. contesti NLP con modelli
Bag-of-Words).

  -------------------------------------------------------------------------------------
  Iperparametro     Tipo / Default    Impatto           Descrizione
  ----------------- ----------------- ----------------- -------------------------------
  `alpha`           float / `1.0`     🔴 Alto           Smoothing di Laplace/Lidstone.
                                                        `alpha=1.0` implica lo
                                                        smoothing di Laplace (evita
                                                        probabilità nulle per token non
                                                        incontrati nel train). `0`
                                                        azzera lo smoothing. Provare:
                                                        `[0.01, 0.1, 0.5, 1.0, 5.0]`.

  `fit_prior`       bool / `True`     🟢 Basso          `True` = stima `P(classe)` dai
                                                        dati. `False` = assume una
                                                        distribuzione uniforme a priori
                                                        (utile con classi fortemente
                                                        sbilanciate nel train non
                                                        rappresentative della realtà).
  -------------------------------------------------------------------------------------

## BernoulliNB

Specifico per feature binarie (presenza/assenza di una caratteristica).

  ------------------------------------------------------------------------
  Iperparametro     Tipo / Default    Impatto           Descrizione
  ----------------- ----------------- ----------------- ------------------
  `alpha`           float / `1.0`     🔴 Alto           Come in
                                                        `MultinomialNB`:
                                                        parametro di
                                                        smoothing per
                                                        frequenze pari a
                                                        zero.

  `binarize`        float/None /      🟠 Medio          Soglia per la
                    `0.0`                               binarizzazione
                                                        automatica delle
                                                        feature continue.
                                                        Se `None`, assume
                                                        che i dati siano
                                                        già binarizzati.
                                                        Con `0.0`, ogni
                                                        valore $> 0$
                                                        diventa `1`.

  `fit_prior`       bool / `True`     🟢 Basso          Identico a
                                                        `MultinomialNB`.
  ------------------------------------------------------------------------

## GridSearchCV consigliato

\`\`\`{python} #\| eval: false \# GaussianNB param_grid_gnb =
{'gnb\_\_var_smoothing': \[1e-11, 1e-9, 1e-7, 1e-5, 1e-3\]}

# MultinomialNB (es. combinazione TF-IDF + NB per Text Classification)

param_grid_mnb = { 'mnb\_\_alpha': \[0.01, 0.1, 0.5, 1.0, 2.0, 5.0\],
'mnb\_\_fit_prior': \[True, False\], }


    ---

    # Regressione Lineare — LinearRegression, Ridge, Lasso, ElasticNet

    ## LinearRegression

    Minimizza la somma dei residui quadratici (OLS - *Ordinary Least Squares*) senza applicare alcuna regolarizzazione. Non presenta iperparametri critici di tuning. Da utilizzare quando il numero di feature è nettamente inferiore al numero di campioni e in totale assenza di multicollinearità.

    | Iperparametro | Tipo / Default | Impatto | Descrizione |
    | --- | --- | --- | --- |
    | `fit_intercept` | bool / `True` | 🟢 Basso | `True` = calcola il termine di bias (intercetta). `False` = costringe il modello a passare per l'origine. |
    | `positive` | bool / `False` | Funzionale | Se `True`, forza i coefficienti stimati ad essere non-negativi (vincolo utile in problemi fisici o economici coerenti). |

    ## Ridge — Regolarizzazione L2

    Aggiunge una penalità $L2$ (somma dei quadrati dei pesi) alla funzione di costo OLS. Riduce la magnitudo dei coefficienti verso lo zero senza mai azzerarli completamente. Strumento fondamentale per gestire la multicollinearità.

    | Iperparametro | Tipo / Default | Impatto | Descrizione |
    | --- | --- | --- | --- |
    | `alpha` | float / `1.0` | 🔴 Alto | Forza della regolarizzazione $L2$. `alpha=0` equivale alla regressione lineare classica. Valori di `alpha` elevati spingono i coefficienti verso lo zero. Griglia: `[0.001, 0.01, 0.1, 1, 10, 100, 1000]`. |
    | `fit_intercept` | bool / `True` | 🟢 Basso | Stima il bias. Quasi sempre impostato su `True`. |
    | `solver` | str / `'auto'` | 🟢 Basso | Configura il risolutore matematico in base alla struttura dati. `'svd'` è il più stabile; `'cholesky'` è rapido per matrici dense con $n < p$; `'lsqr'` è indicato per matrici sparse. |

    ## Lasso — Regolarizzazione L1

    Introduce una penalità $L1$ (somma dei valori assoluti dei pesi). Ha la proprietà intrinseca di generare *sparsità*: azzera esattamente i coefficienti delle feature meno rilevanti, effettuando una **feature selection automatica**.

    | Iperparametro | Tipo / Default | Impatto | Descrizione |
    | --- | --- | --- | --- |
    | `alpha` | float / `1.0` | 🔴 Alto | Forza della regolarizzazione $L1$. Valori grandi aumentano l'aggressività della feature selection eliminando più variabili. Griglia: `[0.0001, 0.001, 0.01, 0.1, 1, 10]`. |
    | `max_iter` | int / `1000` | 🟢 Basso | Iterazioni massime per l'algoritmo di *coordinate descent*. Aumentare in caso di `ConvergenceWarning`. |
    | `selection` | str / `'cyclic'` | 🟢 Basso | `'cyclic'`: aggiorna i coefficienti in ordine sequenziale. `'random'`: selezione casuale ad ogni iterazione, accelera la convergenza su dataset grandi. |

    ## ElasticNet — Combinazione L1 + L2

    Combina linearmente entrambe le penalità $L1$ e $L2$. Risulta particolarmente efficace in presenza di gruppi di variabili fortemente correlate (*grouping effect*), dove Lasso tenderebbe a selezionarne solo una casualmente.

    | Iperparametro | Tipo / Default | Impatto | Descrizione |
    | --- | --- | --- | --- |
    | `alpha` | float / `1.0` | 🔴 Alto | Forza complessiva della regolarizzazione (somma dei termini $L1$ e $L2$). |
    | `l1_ratio` | float / `0.5` | 🔴 Alto | Bilanciamento del mix di regolarizzazione. `0` = equivalente a Ridge puro; `1` = equivalente a Lasso puro; `0.5` = mix equamente ripartito. Griglia: `[0.1, 0.3, 0.5, 0.7, 0.9]`. |

    ## GridSearchCV consigliato

    ::: {.callout-tip}

    ## Efficienza computazionale con RidgeCV/LassoCV

    Per ottimizzare la ricerca, scikit-learn offre le classi specializzate `RidgeCV`, `LassoCV` ed `ElasticNetCV`. Sfruttano l'efficienza algoritmica per calcolare la soluzione sull'intera griglia di `alpha` con un singolo fit, riducendo drasticamente i tempi rispetto a un `GridSearchCV` standard.
    :::

    ```{python}
    #| eval: false
    # Ridge
    param_grid_ridge = {'ridge__alpha': [0.001, 0.01, 0.1, 1, 10, 100, 1000]}

    # Lasso
    param_grid_lasso = {'lasso__alpha': [0.0001, 0.001, 0.01, 0.1, 1, 10]}

    # ElasticNet
    param_grid_en = {
        'en__alpha':    [0.001, 0.01, 0.1, 1],
        'en__l1_ratio': [0.1, 0.3, 0.5, 0.7, 0.9, 1.0],
    }

------------------------------------------------------------------------

# K-Means --- KMeans

## Descrizione

K-Means partiziona lo spazio dei dati in $k$ cluster distinti
minimizzando la varianza intra-cluster, nota come **inerzia**. Il
processo assegna iterativamente ogni punto al centroide più vicino e
ricalcola la posizione dei centroidi stessi. L'algoritmo soffre di una
forte dipendenza dall'inizializzazione casuale e richiede la
predeterminazione del parametro $k$.

## Iperparametri

  ---------------------------------------------------------------------------------
  Iperparametro     Tipo / Default    Impatto           Descrizione
  ----------------- ----------------- ----------------- ---------------------------
  `n_clusters`      int / `8`         🔴 Alto           Numero di cluster $k$. Deve
                                                        essere validato
                                                        esternamente tramite *Elbow
                                                        Method* (inerzia vs $k$),
                                                        *Silhouette Score*, o
                                                        *Davies-Bouldin Index*. La
                                                        scelta ottimale dipende
                                                        fortemente dal dominio
                                                        applicativo.

  `init`            str /             🔴 Alto           `'k-means++'`: strategia di
                    `'k-means++'`                       inizializzazione
                                                        intelligente che posiziona
                                                        i centroidi iniziali il più
                                                        possibile distanti tra
                                                        loro. Previene convergenze
                                                        a minimi locali scadenti
                                                        rispetto a `'random'`.

  `n_init`          int / `'auto'`    🟠 Medio          Numero di inizializzazioni
                                                        indipendenti eseguite (il
                                                        modello finale sceglierà
                                                        quella con inerzia minima).
                                                        Con `'auto'`, scikit-learn
                                                        imposta `10` se
                                                        l'inizializzazione è
                                                        `'random'`, e `1` se è
                                                        `'k-means++'`.

  `max_iter`        int / `300`       🟢 Basso          Numero massimo di
                                                        iterazioni per singola
                                                        esecuzione. Il valore di
                                                        default è quasi sempre
                                                        sufficiente per raggiungere
                                                        la convergenza.

  `tol`             float / `1e-4`    🟢 Basso          Tolleranza per determinare
                                                        la convergenza stabilita
                                                        sulla variazione relativa
                                                        della posizione dei
                                                        centroidi.

  `algorithm`       str / `'lloyd'`   🟢 Basso          Algoritmo computazionale.
                                                        `'lloyd'`: classico
                                                        Expectation-Maximization.
                                                        `'elkan'`: sfrutta la
                                                        disuguaglianza triangolare
                                                        per accelerare i calcoli su
                                                        dataset aventi cluster ben
                                                        definiti e separati.

  `random_state`    int / `None`      🟢 Basso          Seed per garantire la
                                                        riproducibilità della
                                                        scelta dei centroidi
                                                        iniziali.
  ---------------------------------------------------------------------------------

::: callout-tip
## Criteri di scelta del numero di cluster $k$

1.  **Elbow Method**: Ispezionare il grafico dell'inerzia in funzione di
    $k$ e individuare il punto di flesso ("gomito").
2.  **Silhouette Score**: Massimizzare il valore (range teorico da -1 a
    +1).
3.  **Davies-Bouldin Index**: Minimizzare l'indice per ottenere cluster
    compatti e separati.
4.  **Calinski-Harabasz**: Massimizzare l'indice. *Si raccomanda di
    verificare la convergenza di almeno due metriche differenti.*
:::

## Ricerca del k ottimale

\`\`\`{python} #\| eval: false from sklearn.cluster import KMeans from
sklearn.metrics import silhouette_score

results = \[\] for k in range(2, 11): km = KMeans(n_clusters=k,
init='k-means++', n_init=10, random_state=42) labels = km.fit_predict(X)
results.append({ 'k': k, 'inertia': km.inertia\_, 'silhouette':
silhouette_score(X, labels) })


    ---

    # DBSCAN — Density-Based Spatial Clustering

    ## Descrizione

    DBSCAN è un algoritmo di clustering basato sulla densità che non richiede la specificazione a priori del numero di cluster. Identifica i raggruppamenti basandosi sulla continuità spaziale della densità dei punti: un record viene definito *core point* se racchiude un numero minimo di campioni (`min_samples`) entro un raggio di vicinato stabilito (`eps`). I punti non raggiungibili da nessun componente core vengono marchiati come rumore (assegnando la label `-1`). Trova cluster di forma arbitraria.

    ## Iperparametri

    | Iperparametro | Tipo / Default | Impatto | Descrizione |
    | --- | --- | --- | --- |
    | `eps` | float / `0.5` | 🔴 Alto | Raggio del vicinato di un punto. Un valore troppo ridotto confina la quasi totalità dei dati a rumore; un valore eccessivo fonde tutti i punti in un unico grande cluster. Può essere stimato analizzando il *k-distance plot*. |
    | `min_samples` | int / `5` | 🔴 Alto | Numero minimo di punti richiesti all'interno del raggio `eps` affinché l'osservazione si qualifichi come *core point*. Valori bassi generano micro-cluster frammentati. Regola pratica: $2 \cdot n_{features}$ o $dimensioni + 1$. |
    | `metric` | str / `'euclidean'` | 🟠 Medio | Metrica di distanza utilizzata. Come in KNN: `'euclidean'`, `'manhattan'`, `'cosine'`. Per coordinate geografiche impostare `'haversine'`. Per stringhe/sequenze utilizzare metriche dedicate (es. `'levenshtein'`). |
    | `algorithm` | str / `'auto'` | 🟢 Basso | Struttura per il calcolo dei vicini. L'opzione `'brute'` diventa mandatoria qualora si utilizzino metriche di distanza non euclidee personalizzate. |
    | `leaf_size` | int / `30` | 🟢 Basso | Dimensione delle foglie per le strutture ad albero (`kd_tree` o `ball_tree`). Influenza i tempi di calcolo. |
    | `n_jobs` | int / `None` | 🟢 Basso | Livello di parallelizzazione. Impostare su `-1` per sfruttare tutte le CPU. |

    ::: {.callout-tip}

    ## Stima di eps con il k-distance plot

    1. Calcolare la distanza dal $k$-esimo vicino (tipicamente ponendo $k = min\_samples - 1$) per ogni punto del dataset.
    2. Ordinare le distanze ottenute in modo strettamente crescente.
    3. Plottare la curva delle distanze.
    4. Individuare la zona di massima curvatura ("gomito"): il valore sull'asse delle ordinate in quel punto rappresenta una stima ottimale per il parametro `eps`.
    :::

    ## GridSearchCV per DBSCAN

    ::: {.callout-warning}

    ## Limitazioni strutturali

    DBSCAN non espone un metodo `predict()` in senso tradizionale, pertanto l'utilizzo diretto di un oggetto `GridSearchCV` standard fallisce. È necessario implementare un ciclo di ricerca manuale valutando l'ottimalità tramite il Silhouette Score (avendo cura di escludere il rumore dal calcolo della metrica).
    :::

    ```{python}
    #| eval: false
    import numpy as np
    from sklearn.cluster import DBSCAN
    from sklearn.metrics import silhouette_score

    best_score, best_params = -1, {}

    for eps in [0.1, 0.3, 0.5, 0.7, 1.0]:
        for min_s in [3, 5, 7, 10]:
            db = DBSCAN(eps=eps, min_samples=min_s).fit(X)
            labels = db.labels_
            
            # Calcolo dei cluster effettivi escludendo il rumore (-1)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            if n_clusters < 2: 
                continue
                
            # Escludi i punti marchiati come rumore dal calcolo della silhouette
            mask = labels != -1  
            score = silhouette_score(X[mask], labels[mask])
            
            if score > best_score:
                best_score = score
                best_params = {'eps': eps, 'min_samples': min_s}

------------------------------------------------------------------------

# PCA --- Principal Component Analysis

## Descrizione

La PCA è una tecnica di apprendimento non supervisionato deputata alla
riduzione della dimensionalità lineare. Il suo scopo è proiettare i dati
originari in un nuovo spazio cartesiano le cui coordinate --- dette
componenti principali --- sono ortogonali e allineate lungo le direzioni
di massima varianza dei dati. Viene largamente impiegata come fase di
preprocessing per abbattere il numero di feature, rimuovere la
multicollinearità latente e consentire la visualizzazione grafica di
dati ad alta dimensionalità.

## Iperparametri

  ----------------------------------------------------------------------------------------------
  Iperparametro      Tipo / Default       Impatto           Descrizione
  ------------------ -------------------- ----------------- ------------------------------------
  `n_components`     int/float/str/None   🔴 Alto           Numero di componenti da estrarre.
                                                            int: valore fisso. float (0-1):
                                                            quota di varianza totale da spiegare
                                                            (es. `0.95` estrae il numero minimo
                                                            di componenti atte a garantire il
                                                            95% della varianza complessiva).
                                                            `'mle'`: stima automatica di Minka.
                                                            `None`:
                                                            $\min(n_{samples}, n_{features})$.

  `svd_solver`       str / `'auto'`       🟠 Medio          Algoritmo per la decomposizione SVD.
                                                            `'full'`: calcolo esatto (ideale per
                                                            matrici piccole). `'randomized'`:
                                                            algoritmo stocastico di Halko,
                                                            drammaticamente più veloce su
                                                            dataset massivi. `'arpack'`: per
                                                            matrici sparse.

  `whiten`           bool / `False`       🟠 Medio          Se `True`, riscala i coefficienti di
                                                            proiezione per garantire che ogni
                                                            componente presenti varianza
                                                            unitaria. Rimuove la scala relativa
                                                            ed è caldamente raccomandato se a
                                                            valle della PCA si posizionano
                                                            modelli sensibili alla scala come
                                                            KNN o SVM.

  `tol`              float / `0.0`        🟢 Basso          Tolleranza di convergenza per il
                                                            risolutore `'arpack'`.

  `iterated_power`   int/str / `'auto'`   🟢 Basso          Numero di iterazioni per il solver
                                                            `'randomized'`. Più iterazioni
                                                            aumentano l'accuratezza a scapito
                                                            del tempo computazionale.

  `random_state`     int / `None`         🟢 Basso          Seed per rendere riproducibili i
                                                            risultati in caso di utilizzo del
                                                            solver `'randomized'`.
  ----------------------------------------------------------------------------------------------

::: callout-tip
## Analisi della Varianza Spiegata Cumulata

Una best practice consolidata prevede il plotting della varianza
spiegata cumulata in funzione del numero di componenti. L'analista
seleziona il punto in cui la curva si stabilizza (solitamente
intercettando una quota pari al 90-95% della varianza totale). Questo
comportamento può essere automatizzato impostando direttamente il
parametro `n_components=0.95`.
:::

## Utilizzo in pipeline

\`\`\`{python} #\| eval: false from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline from sklearn.preprocessing import
StandardScaler from sklearn.svm import SVC from sklearn.model_selection
import GridSearchCV

# Definizione della Pipeline: Scaler + PCA + Classificatore

pipe = Pipeline(\[ ('scaler', StandardScaler()), ('pca',
PCA(n_components=0.95, random_state=42)), ('svc', SVC(C=1.0,
kernel='rbf')),\])

# Configurazione della griglia includendo la ricerca sul preprocessing della PCA

param_grid = { 'pca\_\_n_components': \[0.80, 0.90, 0.95, 0.99, None\],
'svc\_\_C': \[0.1, 1, 10\], 'svc\_\_gamma': \['scale', 'auto'\], }

grid = GridSearchCV(pipe, param_grid=param_grid, cv=5)

\`\`\`

------------------------------------------------------------------------

# Tabella Riepilogativa --- Quando usare quale algoritmo

  -----------------------------------------------------------------------------------------
  Algoritmo      Task              Dataset        Pro                  Contro
  -------------- ----------------- -------------- -------------------- --------------------
  **KNN**        Classif. /        Piccolo        Semplice, nessuna    Computazionalmente
                 Regressione       ($< 10k$)      fase di training     lento in predict,
                                                  esplicita.           estremamente
                                                                       sensibile alla scala
                                                                       delle feature.

  **SVM (kernel  Classificazione   Medio          Performance          Scalabilità ridotta,
  rbf)**                           ($< 100k$)     eccellenti anche con lento su dataset di
                                                  spazi di feature     grandi dimensioni.
                                                  ridotti.             

  **Decision     Classif. /        Qualsiasi      Elevata              Forte tendenza
  Tree**         Regressione                      interpretabilità     all'overfitting in
                                                  intrinseca, non      assenza di potatura
                                                  richiede lo scaling  o vincoli.
                                                  dei dati.            

  **Random       Classif. /        Medio / Grande Estremamente         Minore
  Forest**       Regressione                      robusto, offre una   interpretabilità
                                                  stima nativa della   rispetto al singolo
                                                  feature importance.  albero, predizioni
                                                                       più lente.

  **Gradient     Classif. /        Medio / Grande Spesso si rivela il  Fase di
  Boosting**     Regressione                      modello predittivo   addestramento
                                                  più accurato in      sequenziale lenta,
                                                  assoluto su dati     richiede un
                                                  tabulari.            fine-tuning accurato
                                                                       di molti
                                                                       iperparametri.

  **Logistic     Classificazione   Qualsiasi      Estremamente veloce, Limitatamente
  Reg.**                                          fornisce probabilità confinato a confini
                                                  calibrate            di decisione
                                                  nativamente.         strettamente
                                                                       lineari.

  **Naive        Classificazione   Grande / Testo Velocità             L'assunzione di
  Bayes**                                         computazionale       indipendenza
                                                  straordinaria,       condizionale è
                                                  ideale per domini    spesso irrealistica.
                                                  NLP.                 

  **Ridge /      Regressione       Qualsiasi      Altamente            Vincolato
  Lasso**                                         interpretabile,      all'ipotesi di
                                                  strutturato con      relazioni puramente
                                                  regolarizzazione     lineari tra le
                                                  interna.             variabili.

  **K-Means**    Clustering        Medio / Grande Computazionalmente   Richiede la
                                                  rapido e altamente   predeterminazione di
                                                  scalabile.           $k$, confinato alla
                                                                       rilevazione di
                                                                       cluster sferici.

  **DBSCAN**     Clustering        Piccolo /      Isola cluster di     Estremamente
                                   Medio          forma geometrica     sensibile alla
                                                  arbitraria, rileva   calibrazione dei
                                                  ed esclude il        parametri `eps` e
                                                  rumore.              `min_samples`.

  **PCA**        Riduzione         Alta           Rimuove              I componenti
                 dimensione        dimensione     efficacemente la     estratti risultano
                                                  ridondanza           di complessa
                                                  informativa e la     interpretazione
                                                  collinearità.        rispetto alle
                                                                       feature originarie.
  -----------------------------------------------------------------------------------------
