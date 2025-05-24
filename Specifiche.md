# SRM - Students Relationship Management
## Specifiche del Progetto

### Introduzione
L’obiettivo di questo progetto è realizzare un sistema per la gestione delle relazioni didattica tra il docente e i suoi studenti: ciò deve avvenire tramite la gestione dei vari aspetti che compongono la relazione di natura didattica docente-studente. 
Il sistema non deve solo permettere di gestire questi aspetti (come ad esempio permettere ad uno studente di prenotarsi per un ricevimento) ma ne deve anche tenere traccia nel tempo, in modo da rendere disponibile uno storico per ogni studente al quale il professore può accedere in qualsiasi momento 

## Requisiti Funzionali
### Accesso alla piattaforma
L'accesso al sistema avviene tramite l'inserimento del proprio indirizzo mail universitario, al quale il sistema invierà un link di accesso. In particolare:
- Se l'indirizzo email inserito corrisponde a quello del **docente**, il link nella mail avrà durata infinita e reindirizzerà il docente ad una pagina di login per inserire *username* e *password*. Se le credenziali saranno corrette, il docente accederà alla parte amministrativa del sito.
- In caso l'accesso venga eseguito da uno **studente**, il sistema invierà all'indirizzo mail fornito un link di accesso temporaneo della durata di 15 minuti. Il link poi reindirizzerà lo studente ad una pagina di login in cui dovrà inserire i propri dati universitari, come *matricola*, *nome* e *cognome*, in modo da poter essere registrato.

### Slot di disponibilità appuntamenti (docente)
Il sistema dovrà permettere al docente di gestire le proprie disponibilità per i vari appuntamenti di natura didattica con gli studenti. Il docente deve avere la possibilità di inserire sia eventi *singoli*, ovvero che valgono per una singola giornata, sia eventi *ricorrenti*. Per quanto riguarda gli eventi ricorrenti, la ricorrenza deve essere possibile per ogni giorno, settimana o mese. Inoltre, il termine per ogni ricorrenza può essere specificato o tramite un conteggio di ricorrenze o tramite una data di termine.

### Tipi di eventi (docente)
Il docente potrà creare eventi di diverso tipi, a seconda della funzione che devono avere. Ad esempio, possono essere creati eventi di tipo:
- **Ricevimento**: dedicati al ricevimento studenti
- **Esame**: dedicati agli esami orali
- **Tirocinio**: dedicati a tirocinanti e/o tesisti per i quali magari è richiesto più tempo rispetto ad un normale ricevimento

### Tipi di slot (docente)
Al mommento della creazione di un evento, il docente dovrà poter scegliere come organizzare i relativi slot di disponibilità. Più precisamente potrà scegliere tra:
- **Slot Singoli**: in caso il docente crei slot *singoli*, allora questi saranno resi disponibili per la prenotazione singolarmente, dando la possibilità allo studente di scegliere liberamente quale slot prenotare, anche se vi sono slot con una data di inizio precedente
- **Multi-Slot**: i multi-slot invece, rendono disponibili per la prenotazione soltanto i primi slot liberi (in ordine cronologico). Utilizzando questo tipo di organizzazione degli slot, si eviterà la creazione di "buchi" all'interno delle prenotazioni.

### Follow-Up (docente)
Il sistema deve permettere al docente di insererire, una volta terminato un appuntaento, una piccola nota relativa a tale appuntamento.

### Registro interazioni (docente)
Per ogni studente, il sistema ne deve registrare le attività per rendere disponibile al docente, in qualisasi momento, il profilo di ogni studente che conterrà lo storico delle interazioni col docente. Inoltre il docente potrà aggiungere ad ogni studente i tag che abilitino le prenotazioni dei vari tipi di slot di disponibilità. 

### Prenotazione ricevimento (studente)
La prenotazione di un ricevimento da parte di uno studente deve avvenire, ovviamente, all'interno di uno slot di disponibilità creato dal relativo docente e la prenotazione deve avvenire almeno con 48h di anticipo. Per cui, anche in presenza di slot disponibili, scadute queste 48h il sistema non li renderà disponibili per la prenotazione.
Ad ogni studente saranno resi visibili i primi 10 slot disponibili.

### Permessi di uno studente (studente)
Il sistema dovrà far sì che gli studenti possano prenotare gli slot soltanto dei tipi per i quali sono abilitati. Ad esempio, solo studenti che sono registrati nel sistema dal docente come "Tirocinanti" potranno prenotare slot di tipo *Tirocinio*. 
Ogni studente inoltre potrà avere un numero massimo di prenotazioni attive, che varierà in base al tipo di slot prenotati. 

### Cancellazione ricevimento (studente)
La cancellazione di un ricevimento deve essere possibile fino a 24 ore prima

### Reminder
Sia per lo studente che per il docente, il sistema dovrà occuparsi di mandare una notifica tramite mail il giorno prima del ricevimento, indicando luogo, orario.  