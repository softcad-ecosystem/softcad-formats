**Technical RC1 query-language notes only. Not a released runtime or validated public API.**

**Technical RC1 query-language notes only. Not a released runtime or validated public API.**

# Interogări TDB3

Un limbaj de întrebări pentru baza TDB3, scris ca un șir de pași care se citesc
de la stânga la dreapta, exact în ordinea în care se întâmplă:

```
parcele
| unde localitate = "Tureni" și suprafata > 500
| sortează suprafata desc
| primele 10
| alege nr: cheie(), proprietar, ha: suprafata / 10000
```

În SQL, aceeași întrebare începe cu ce iese (`SELECT`) și abia apoi spune de
unde (`FROM`), cu filtrul la mijloc și ordinea la coadă. Aici fiecare pas
primește rândurile pasului dinainte. Se poate scrie pe un rând sau pe mai
multe, și se poate opri oriunde: `parcele | unde …` e deja o interogare.

---

## Într-un minut

```
parcele | numără
parcele | unde proprietar ~ "fratauteanu*"               # fără diacritice și majuscule
parcele | unde incepe_cu(nr, "47003")
parcele | unde "Popa Maria" în coproprietari             # într-o listă
parcele | unde adresa.localitate = "Cluj"                # câmp adânc
parcele | grupează localitate { n: număr(), total: sumă(suprafata) }
parcele | sortează proprietar | distincte proprietar
parcele @-1 | unde cheie() = 47003                       # cum era înainte de ultima salvare
parcele @"2026-09-01" | numără                           # cum era la o dată
parcele.. | alege k: cheie(), tip                        # ce s-a schimbat la ultima salvare
parcele @20..@30 | unde tip = "șters"                    # între două înscrieri
parcele | leagă proprietari pe proprietar ca p | alege nr: cheie(), tel: p.telefon
```

Cuvintele limbajului merg **în română sau în engleză, cu diacritice sau fără,
cu litere mari sau mici**. `sortează`, `sorteaza`, `SORTEAZA` și `sort` sunt
același pas. Numele câmpurilor rămân exact cum sunt în date.

---

## Sursa

| Scris | Ce dă |
|---|---|
| `parcele` | tabela, cum e acum |
| `parcele @25` | cum era la înscrierea 25 |
| `parcele @-1` | cum era înainte de ultima salvare (`@-3`: cu trei salvări în urmă) |
| `parcele @"2026-09-01"` | cum era la sfârșitul acelei zile |
| `parcele @"16.10.2026 14:30"` | cum era la acel minut |
| `parcele @"a3f9c2"` | la înscrierea cu amprenta care începe așa |
| `parcele @$cand` | momentul dat ca parametru (număr, dată, sau o `Inscriere`) |
| `parcele @20..@30` | **ce s-a schimbat** de la înscrierea 20 la 30 |
| `parcele @20..` | ce s-a schimbat de la 20 până acum |
| `parcele..` | ce s-a schimbat la ultima salvare |

Contopirile făcute de baza însăși (jurnalul mutat în arbore) nu se numără ca
salvări la `@-1`: nu schimbă nimic din conținut.

Un rând de diferență are trei câmpuri: `tip` („adăugat”, „modificat”,
„șters”), `inainte` și `dupa`. Cheia rândului se ia tot cu `cheie()`:

```
parcele @20.. | unde tip = "modificat" și inainte.proprietar != dupa.proprietar
             | alege nr: cheie(), de_la: inainte.proprietar, la: dupa.proprietar
```

## Pașii

| Pas | În engleză | Ce face |
|---|---|---|
| `unde <condiție>` | `where` | păstrează rândurile pentru care condiția e adevărată |
| `alege a, b, nume: expr, *` | `select` | rânduri noi, doar cu ce alegi; `*` aduce tot rândul |
| `sortează expr [desc], …` | `sort` | ordonează (vezi „Ordinea” mai jos) |
| `primele N` | `take`, `limit` | primele N rânduri |
| `sari N` | `skip` | sare peste N rânduri |
| `grupează chei { nume: agregat, … }` | `group` | un rând pe grup; fără acolade numără |
| `distincte a, b` | `distinct` | combinațiile diferite, o dată fiecare |
| `numără` | `count` | un singur rând: `{n: …}` |
| `leagă tabel pe expr ca nume` | `join … on … as` | aduce rândul din altă tabelă, după cheie |
| `leagă tabel.index pe expr ca nume` | | aduce **lista** rândurilor găsite prin index |

`alege` dă singur nume câmpurilor simple: `alege proprietar, adresa.localitate`
face câmpurile `proprietar` și `localitate`. O expresie oarecare cere nume:
`alege ha: suprafata / 10000`.

`grupează` fără chei face un singur grup din toată tabela; dacă nu e niciun
rând, tot iese un rând (`{n: 0}`), ca la orice numărătoare.

`leagă` nu pierde rânduri: dacă nu găsește perechea, câmpul e `nimic`
(sau lista e goală).

## Expresiile

- **Câmpuri:** `proprietar`, `adresa.localitate`, `coproprietari[0]`,
  `` `nr cadastral` `` (între accente grave, pentru nume cu spații sau care
  sunt cuvinte rezervate).
- **Cheia și tot rândul:** `cheie()` — cheia rândului (o listă, dacă cheia e
  compusă: `cheie()[0]`); `valoare()` — tot rândul.
- **Valori:** `500`, `1520.4`, `1e3`, `"text"`, `'text'`, `„text”`,
  `adevărat`/`true`, `fals`/`false`, `nimic`/`null`, `[1, 2, 3]`.
- **Parametri:** `$nume`, dați din program. Valoarea nu trece niciodată prin
  textul interogării, deci nu se poate „strecura” cod în ea.
- **Operatori**, de la cel mai slab la cel mai tare:

| | |
|---|---|
| `sau` / `or` | |
| `și` / `and` | |
| `nu` / `not` | |
| `=` `==` `!=` `<>` `<` `<=` `>` `>=` `~` `în` `nu în` | comparații |
| `+` `-` | `+` adună și texte, și liste |
| `*` `/` `%` | |
| `-x` | |

Comentariile încep cu `#` sau `//` și țin până la capătul rândului.

## Ce înseamnă — ales ca să nu surprindă

- **Un câmp care lipsește e `nimic`.** `x = nimic` e adevărat când x lipsește
  sau e nimic. Orice comparație cu `nimic` e falsă, iar `nu` întoarce exact:
  `nu (suprafata > 100)` prinde și rândurile fără suprafață. SQL are aici o
  logică cu trei valori, în care `NOT (x > 100)` *nu* e opusul lui `x > 100`
  — o sursă veche de rânduri pierdute pe tăcute.
- **Se compară doar lucruri de același fel:** numere cu numere (întregi și
  reali amestecați: `5 = 5.0`), text cu text. `suprafata < "z"` e fals pentru
  orice număr — nu o eroare și nu o conversie ascunsă.
- **Aritmetica pe ce nu e număr dă `nimic`**, la fel împărțirea la zero. Un
  rând ciudat nu oprește o interogare peste o mie de rânduri bune.
- **`~` compară fără diacritice și fără majuscule, cu `*` și `?`:**
  `proprietar ~ "pop*"` găsește „Popescu”, „POPA”, „Popovici”;
  `"fr?tauti"` găsește „Frătăuți”; `ș`/`ş` și `ț`/`ţ` sunt aceeași literă.
- **`în` caută într-o listă:** `"Popa" în coproprietari`,
  `localitate în ["Tureni", "Turnu"]`. Pentru „conține textul” e funcția
  `contine(nume, "pop")`.

### Ordinea

`sortează` ordonează ca omul, nu ca mașina:

- după **alfabetul românesc**: `a < ă < â < b`, `s < ș < t`, `t < ț < u`; fără
  să țină cont de majuscule;
- **numerele din text după valoare**: „Parcela 2” < „Parcela 2a” < „Parcela 10”;
- numerele înaintea textelor; **valorile lipsă la coadă**, și la `desc`.

SQLite pune „Ștefan” după „Zamfir” și „Parcela 10” înaintea lui „Parcela 2”.

Fără `sortează`, rândurile vin **în ordinea cheii** — oricum ar fi fost găsite.

## Funcțiile

| Funcția | În engleză | |
|---|---|---|
| `cheie()` | `key()` | cheia rândului |
| `valoare()` | `value()` | tot rândul |
| `exista(câmp)` | `exists` | câmpul e în rând (chiar dacă e `nimic`) |
| `lungime(x)` | `len`, `length` | de text, listă, dicționar |
| `incepe_cu(x, "P")` | `starts_with` | |
| `se_termina_cu(x, "escu")` | `ends_with` | |
| `contine(x, "pop")` | `contains` | text în text, sau element în listă |
| `normalizat(x)` | `normalized` | fără diacritice și majuscule |
| `mici(x)`, `mari(x)` | `lower`, `upper` | |
| `rotunjit(x, 2)` | `round` | **ca la școală**: 2,5 → 3, nu ca în bancă (2,5 → 2) |
| `abs(x)` | | |
| `numar_din("1.520,40")` | `number` | număr din text, cu virgulă sau punct zecimal |
| `text(x)` | `str` | |
| `tip(x)` | `type` | „număr”, „text”, „listă”, „dicționar”, „nimic”… |
| `daca(c, a, b)` | `if` | |
| `implicit(x, 0)` | `default` | x, sau 0 dacă x lipsește |
| `cel_mai_mic(a, b, …)`, `cel_mai_mare(…)` | `least`, `greatest` | |

**Agregatele** — doar în acoladele lui `grupează`: `număr()` (rândurile) sau
`număr(x)` (cele cu x), `sumă(x)`, `medie(x)`, `min(x)`, `max(x)`, `listă(x)`,
`distincte(x)`, `primul(x)`, `ultimul(x)` (în engleză: `count`, `sum`, `avg`,
`min`, `max`, `list`, `distinct`, `first`, `last`). Se pot combina:
`{ medie_ha: rotunjit(medie(suprafata) / 10000, 2) }`.

`sumă` adună realii **exact** (`math.fsum`): zece rânduri de 0,1 dau 1,0, nu
0,9999999999999999 — o mie de suprafețe adunate nu pierd centimetri din
cauza ordinii în care vin.

## Indexurile se aleg singure

Planificatorul se uită la condițiile din `unde`-urile de la început și
caută cel mai ieftin drum:

| Condiția | Drumul |
|---|---|
| `cheie() = 47003`, `cheie() în [..]` | citire directă după cheie |
| `cheie() >= 100 și cheie() < 200`, `cheie()[0] = "Tureni"` | interval de chei |
| `câmp = v`, `câmp în [..]`, `v în câmp` | index pe câmp (și pe liste) |
| `câmp > v`, `câmp <= v`, … | interval în index |
| `localitate = "Tureni" și suprafata > 500` | index pe (localitate, suprafață) |
| `incepe_cu(câmp, "Pop")` | interval în index — și în cel fără diacritice |
| `câmp ~ "pop*"`, `câmp ~ "popa"` | index fără diacritice |
| `A sau B` | reuniunea drumurilor lui A și B, dacă amândouă au unul |

Alege după numărători luate din arbore, fără să citească rânduri: fiecare
trimitere din arbore știe câte intrări are sub ea, deci „câți candidați are
intervalul ăsta” costă câteva noduri, oricât de mare ar fi intervalul. Dacă
indexul ar aduce mai mult de o treime din tabelă, parcurge tabela.

**Garanția: drumul ales nu schimbă rezultatul.** Un index dă doar candidați;
condiția întreagă se verifică apoi pe fiecare rând. Iar rândurile vin în
ordinea cheii pe orice drum. Testele o verifică: mii de interogări aleatoare
pe date alese să fie rele (vezi „Ce s-a probat”), fiecare rulată cu
planificator și fără, cu rezultate identice rând cu rând.

Mai face două lucruri singur:

- **decodează doar ce trebuie**: `parcele | unde nr % 7 = 3 | numără`
  citește din fiecare rând doar câmpul `nr`; `grupează localitate` doar
  `localitate`. Rândul întreg se construiește numai când iese întreg;
- **ține în memorie doar cât trebuie**: `sortează … | primele 10` păstrează
  10 rânduri, nu toată tabela.

`explică` arată ce ar face, fără să ruleze nimic:

```
>>> print(db.explica('parcele | unde proprietar ~ "pop*" și suprafata > 500 '
...                  '| sortează suprafata desc | primele 5'))
parcele, starea de acum (înscrierea 52)
  acces: index „prop”: proprietar ~ „pop*” (~20.391 candidați)
  unde proprietar ~ „pop*” și suprafata > 500
  sortează suprafata desc → primele 5 (ține în memorie doar 5)
```

## Greșelile

Cu locul exact și, când se poate, cu ce ai vrut să scrii:

```
pas necunoscut „sorteza” — ai vrut „sortează”? Pașii sunt: unde, alege, … (linia 1, coloana 11)
  parcele | sorteza suprafata
            ^
nu există tabela „parcel” — ai vrut „parcele”? (linia 1, coloana 1)
```

O bază fără schemă nu poate refuza un câmp scris greșit — dar îl poate
semnala. Pe o interogare care nu găsește nimic:

```
>>> r = db.interogheaza('parcele | unde propietar = "Albu"')
>>> r.lista()
[]
>>> r.avertismente()
['câmpul „propietar” nu apare în niciun rând — ai vrut „proprietar”?']
```

Mesajele sunt în română; `Interogare(text, limba="en")` le dă în engleză.

## Din program

```python
from tdb3 import Baza, Interogare

db = Baza("lucrari.tdb3")
for p in db.interogheaza("parcele | unde proprietar ~ $cine | primele 20", cine="pop*"):
    print(p)

q = Interogare("parcele | unde localitate = $l | numără")   # citită o dată
for loc in ["Tureni", "Turnu"]:
    print(loc, q.ruleaza(db.stare(), {"l": loc}).lista())

vechi = db.stare(list(db.istoric())[10])
vechi.interogheaza("parcele | numără")                      # pe orice stare

with db.scrie(autor="Crinel") as tx:
    tx.tabel("parcele").pune(47010, {"proprietar": "Popovici"})
    tx.interogheaza('parcele | unde proprietar ~ "pop*"')   # vede și 47010
```

O interogare dintr-o tranzacție vede scrierile ei încă neînscrise, iar
rândurile pe care le citește se țin minte: dacă altcineva le schimbă până la
înscriere, tranzacția primește conflict, ca la `get()`. (Un rând *nou* care
s-ar potrivi condiției nu e conflict — ca în majoritatea bazelor de date.)

## Ce nu face încă

- **Scrieri prin limbaj** (`… | actualizează categorie = "arabil"`,
  `… | șterge`): acum, scrierile se fac din program.
- **Citirea direct din index**, fără rând, când interogarea cere doar
  câmpurile indexului; azi fiecare candidat se citește din tabelă (și se
  verifică față de index).
- **Legarea în TSS**, ca un script să poată pune întrebări bazei.
- **Viteza**: vezi `CITESTE.md` — compilat, căutările prin index sunt de
  15–40 de ori mai lente decât în SQLite, iar parcurgerile de 25–40 de ori;
  „începe cu” e mai rapid. Drumul e un miez nativ care citește același
  fișier.
