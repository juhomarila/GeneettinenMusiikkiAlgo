import numpy as np
import random

#lukujen formationtia
formatters = {
    'int': lambda x: '%4d' % x,
    'float': lambda x: '%.02f' % x
}

# apumetodi sus-metodin tulostamiseen
def printReport(population, fitness, wheel, selectors, selected_individuals):
        print('       Populaatio:', population)  
        print('         Arvosana:', fitness)

        # vanhemmille omat rulettinumerot kumulatiivisella arvosanan summalla
        # esim. 4 vanhempaa [5 15 20 30] 
        print('   Rulettinumerot:', wheel)       
        # jos ensimmäinen osuma on vaikkapa 6.45 valitaan vanhempi 1 eli arrayn toinen vanhempi
        print('   Ruletin osumat:', selectors)
        print('Valitut vanhemmat:', selected_individuals)

# metodi sus on stokastisen ruletin metodi, joka palauttaa valitut vanhemmat
# parametrit rng, population, fitness, size = 
# randomi numero, populaatio, populaation jäsenien henk.koht arvosana, populaation koko
def sus(rng: np.random.Generator,
        population: np.ndarray,
        fitness: np.ndarray,
        size: int) -> np.ndarray:
    if size > len(population):
        raise ValueError

    fitness_cumsum = fitness.cumsum()
    fitness_sum = fitness_cumsum[-1]  # rulettipöytä

    # ruletin "pallo" tai tässä tilanteessa enemmänkin onnenpyörän n määrän merkkinuolien
    # etäisyys toisistaan luodaan fitnessin summan ja populaation määrän jakolaskulla
    step = fitness_sum / size  

    # randomi aloituspaikka, josta siirrytään eteenpäin
    start = rng.random() * step  

    # ruletin osumat
    selectors = np.arange(start, fitness_sum, step)

    # etsii valitut vanhemmat arraysta ja se palauttaa tiedon ketkä valittiin
    selected = np.searchsorted(fitness_cumsum, selectors)
    printReport(population, fitness, fitness_cumsum, selectors, selected)
    return selected

# Metodi selectedToPairs jakaa vanhemmat kahteen eri arrayhin, isiin ja äiteihin
# parametrit selected, array = selecter(stokastisen ruletin valitsemat vanhemmat), 
# array(alkuperäinen luotu numeropohjainen array jossa vanhemmat)
def selectedToPairs(selected, array):
    parents = []
    for i in range(len(array)):
        for index, item in enumerate(array):
            try:
                if index == selected[i]:
                    parents.append(array[index][:-1])
             
            except(ValueError,IndexError):
                pass
        i += 1

    print("Vanhemmat:")
    a = 0
    for i in range(len(parents)):
        print("v", i+1, ":", parents[i])
        a += 1

    # luodaan kaksi erillistä arrayta, m = äidit, d = isät
    m = parents[:len(parents)//2]
    d = parents[len(parents)//2:]
    return m, d

# Metodi crossover suorittaa pariutumisen isien ja äitien kesken
# parametrit m, d = äiti, isä
def crossover(m, d):

    # vanhemmat saavat aina kaksi lasta c1, c2, jotta populaatio ei pienene
    c1, c2 = [], []

    if random.random() < 0.94: # todennäköisyys pariutumiselle 94%
        x = random.randint(1, len(m)-1) # satunnainen kohta listasta mistä vaihdetaan geenit
        print("Geenien vaihtokohta:", x)
        c1.append(m[:x] + d[x:])
        c2.append(d[:x] + m[x:])

    # jos vanhemmat eivät pidäkään toisista eli pariutumista ei tapahdu (tod.näk 6%)
    # lapsi 1(c1) on äitinsä ja lapsi 2(c2) on isänsä
    else:
        c1.append(m)
        c2.append(d)
    children = c1 + c2
    return children

# Metodi mutation aiheuttaa geenienvaihtoa lasten sisällä (jotkin geenit vaihtavat paikkaa)
# parametrit children = metodin crossover luomat lapset
# palauttaa mutatoidut lapset
def mutation(children):

    # jaetaan lapset kahteen ryhmään joiden välilä geenit vaihtuvat
    c1 = children[:len(children)//2]
    c2 = children[len(children)//2:]
    # iteroidaan lapset läpi
    for i in range(len(c1)):
        if random.random() < 0.05: #5% todennäköisyydellä
            x = random.randint(0, len(c1[i])-1)
            c1[i][x], c2[i][x] = c2[i][x], c1[i][x] #geeni listan paikasta x vaihtaa lapsen c1 ja c2 välillä paikkaa
        else:
            c1 = c1
            c2 = c2
        if random.random() < 0.02: #2% todennäköisyydellä
            x = random.randint(0, len(c1[i])-1)
            y = random.randint(0, len(c1[i])-1)
            c1[i][x], c1[i][y] = c1[i][y], c1[i][x] #geeni listan paikasta x ja listan paikasta y vaihtaa yksittäisen lapsen kohdalla paikkaa
        else:
            c1 = c1
        if random.random() < 0.02: #2% todennäköisyydellä
            x = random.randint(0, len(c2[i])-1)
            y = random.randint(0, len(c2[i])-1)
            c2[i][x], c2[i][y] = c2[i][y], c2[i][x] #geeni listan paikasta x ja listan paikasta y vaihtaa yksittäisen lapsen kohdalla paikkaa
        else:
            c2 = c2
        if random.random() < 0.02: #2% todennäköisyydellä
            x = random.randint(0, len(c1[i])-2)
            c1[i][x], c1[i][x+1] = c1[i][x+1], c1[i][x] #kaksi vierekkäistä geeniä paikassa x ja x+1 vaihtavat yksittäisen lapsen sisällä paikkaa
        else:
            c1 = c1
        if random.random() < 0.02: #2% todennäköisyydellä
            x = random.randint(0, len(c2[i])-2)
            c2[i][x], c2[i][x+1] = c2[i][x+1], c2[i][x] #kaksi vierekkäistä geeniä paikassa x ja x+1 vaihtavat yksittäisen lapsen sisällä paikkaa
        else:
            c2 = c2

    children = c1 + c2
    return children

# Metodi addRandomGene lisää tiettyyn lapseen geenin annetusta geenipoolista matalalla todennäköisyydellä
def addRandomGene(children):
    choose = [28, 29, 30, 31, 32, 33, 34, 35] # mahdolliset lisättävät geenit (a-molli edelleen kyseessä) tämä onkin se suurin kehittmiskohde, jotta voi valita muita sävellajeja.
    for i in range(len(children)):
        if random.random() < 0.02: # 2% todennäköisyydellä
            note = random.choice(choose) # valitaan randomi nuotti choose-listasta
            x = random.randint(0, len(children[i])-1) #valitaan randomi paikka mihin randomi nuotti lisätään
            children[i][x] = note
        else:
            children[i] = children[i]

    return children





  
