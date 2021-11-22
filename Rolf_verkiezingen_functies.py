import pandas as pd
from flask import Flask

df = pd.read_csv(r'C:/Users/Braba/Downloads/Uitslag_alle_gemeenten_TK20210317.csv', sep=';')

# localhost:8000/start hoi

# localhost:8000/vvd hoeveel mensen in amsterdam op vvd hebben gestemd
# manier 1, antwoord in int vorm
df[df['RegioNaam'] == 'Amsterdam'].index
df['VVD'][15]

# manier 2, tabelvorm
VVDstemInAmsterdam = df[df['RegioNaam'] == 'Amsterdam'][['RegioNaam', 'VVD']]
VVDstemInAmsterdam

# localhost:8000/rangschikking/vvd volgorde van gemeentes van veel naar weinig voor vvd
dfVVDperGemeente = df[['RegioNaam', 'VVD']].sort_values(['VVD'], ascending=False)
dfVVDperGemeente.head()

# localhost:8000/rangschikking/{vvd} volgorde van gemeentes van veel naar weinig voor keuze
def partijpergemeente(partij='VVD'):
    """
    Deze functie laat het aantal stemmen per Gemeente zien op een partij naar keuze. VVD is de default partij.
    """
    dfPartijpergemeente = df[['RegioNaam', partij]]
    gesorteerd = dfPartijpergemeente.sort_values([partij], ascending=False)
    return gesorteerd

partijpergemeente('D66')

# localhost:8000/geldig/{stad} zien ongeldig vs geldig percentage
def geldigheid1(stad = 'Amsterdam'):
    """
    Deze functie berekent een percentage als numpy.float. Dit is gedaan door de index anders te genereren.
    .index geeft een complexe panda series (class?) terug. Door te indexen op de [0] komt er een numpy.int ipv een series.
    Doordat de index nu een int is, worden geldig en ongeldig ook als int teruggegeven ipv een panda series. Hoe dit komt is niet duidelijk.
    Percentage wordt afgerond op 2 decimalen.
    De return is index, stad, geldig, ongeldig, percentage.
    """
    index = df[df['RegioNaam'] == stad].index[0]
    geldig = df.loc[index, 'GeldigeStemmen']
    ongeldig = df.loc[index, 'OngeldigeStemmen']
    percentage = ongeldig / geldig * 100
    percentage = round(percentage, 2)
    return index, stad, geldig, ongeldig, percentage

geldigheid1('Stein')[4]

# localhost:8000/geldig/ steden in volgorde van percentage ongeldig
def Validity():
    """
    Deze functie berekent het percentage ongeldige stemmen per regio en returnt dit in een dataframe.
    """
    # stap 1: append alle percentages in een list mbv geldigheid1 (al eerder gedefinieerd).
    validPerc = [] * df['RegioNaam'].size
    for regio in df['RegioNaam']:
        var = geldigheid1(regio)[4]
        validPerc.append(var)

    # stap 2: creer een dataframe van regionaam en percentages
    myser = pd.Series(validPerc, name='Geldigheid')
    mydf1 = pd.concat([df['RegioNaam'], myser], axis = 1)

    #mydata = {'RegioNaam': df['RegioNaam'], 'Geldigheid': validPerc}
    #Gelddf = pd.DataFrame(data=mydata)

    # stap 3: sorteer dataframe op ongeldigheid van hoog naar laag
    mydfsorted = mydf1.sort_values(['Geldigheid'], ascending=False)
    return mydfsorted

Validity()

# localhost:8000/uitslag/{gemeente} volgorde van partij
def stem_stad(stad='Amsterdam'):
    """
    Deze functie returnt een dataframe waarin het aantal stemmen per partij van hoog naar laag staan in een meegegeven gemeente. Amsterdam is default.
    """
    df_stemmen = df[list(df.columns[9:])]
    index = df_stemmen[df_stemmen['RegioNaam'] == stad].index[0]
    row = df_stemmen.loc[index][1:]
    data = {'Aantal stemmen': row}
    mydf = pd.DataFrame(data).sort_values(['Aantal stemmen'], ascending=False)
    mydf.index.name = 'Regio'
    return mydf

stem_stad()
# localhost:8000/landelijke uitslag landelijke uitslag
def landelijke_uitslag(data=df):
    """
    Deze functie berekent het totaal aantal zetels per partij op basis van totaal aantal geldige stemmen en verdeling van restzetels.
    Het returnt een dictionary.
    """
    # stap 1: het totaal aantal stemmen en kiesdeler
    totaalStemmen = data['GeldigeStemmen'].sum()
    totaalZetels = 150
    kiesdeler = totaalStemmen / totaalZetels

    # stap 2: het totaal aantal stemmen per partij dat voldoet aan de kiesdeler
    stemmen_per_partij = {}
    for partij in data.columns[10:]:
        if data[partij].sum() > kiesdeler:
            stemmen_per_partij[partij] = data[partij].sum()

    # stap 3: het aantal volledige zetels per partij
    zetels_per_partij = {}
    for partij, aantal_stemmen in stemmen_per_partij.items():
        zetels_per_partij[partij] = aantal_stemmen // kiesdeler 

    # stap 4: verdeling restzetels
    while sum(zetels_per_partij.values()) < totaalZetels:
        hoogste = ['naam', 0]
        for partij, aantal_stemmen in stemmen_per_partij.items():
            aantal_zetels = zetels_per_partij[partij]
            rest = aantal_stemmen / (aantal_zetels + 1)
            if rest > hoogste[1]:
                hoogste[0] = partij
                hoogste[1] = rest
        zetels_per_partij[hoogste[0]] = zetels_per_partij[hoogste[0]] +1
    return zetels_per_partij

landelijke_uitslag()

# flask en endpoints
app = Flask(__name__)

@app.route('/')
def hello_world():
    """
    Deze functie print "Hello, World!".
    """
    return '<p>Hello, World!</p>'

@app.route('/test')
def test():
    """
    Deze functie zet een panda df om in een html tabel. Het print het aantal stemmen op de VVD in Amsterdam in tabel vorm.
    """
    mijn_tabel = VVDstemInAmsterdam.to_html()
    return mijn_tabel

@app.route('/test2/<fractie>') #variable staat tussen tags (html front end) en wordt herkend ondanks dat het hier in een string staat
def partij(fractie):
    """
    Deze functie isoleert de partijnaam die meegegeven is in de endpoint url, 
    sorteert het aantal stemmen op deze partij per gemeente van hoog naar laag, 
    en returnt de data in de vorm van een html tabel.
    """
    for name in df.columns:    #soms onconventionele kolomnamen (volledige partijnaam ipv afkorting), op deze manier wordt SP ook goedgekeurd
        if fractie in name:
            return partijpergemeente(name).to_html()

@app.route('/test3/rangschikking/<stad>')
def rangschikking(stad):
    """
    Deze functie returnt het percentage ongeldige stemmen in een opgegeven stad als string.
    """
    return f"Het percentage ongeldige stemmen in {stad} is {geldigheid1(stad)[4]}%."

@app.route('/test4/rangschikking')
def rangschikking_alles():
    """
    Deze functie returnt het percentage ongeldige stemmen per regio van hoog naar laag in tabel vorm.
    """
    return Validity().to_html()

@app.route('/test5/uitslag/<gemeente>')
def gemeente_uitslag(gemeente):
    """
    Deze functie returnt het aantal stemmen per partij in een opgegeven gemeente van hoog naar laag.
    """
    return stem_stad(gemeente).to_html()

if __name__ == '__main__':
    app.run(port = 8000, debug=True, use_reloader=False)