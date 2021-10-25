"""
Tämä ohjelma on musiikintekoalgoritmi
"""

import math
import numpy
import pyaudio
import itertools
import random
from scipy import interpolate
from operator import itemgetter
from numpy.random import default_rng

from midiutil import MIDIFile

from algo import *

# Musiikinsoittometodit otin suoraan valmiina, eli eivät ole omaa koodiani.
# Tässäkin on jatkokehityskohde, koska tällä hetkellä musiikki
# soi vain tasaisilla väleillä, eikä variaatiota ole.

#### LAINATTU KOODI ALKAA ####
# https://davywybiral.blogspot.com/2010/09/procedural-music-with-pyaudio-and-numpy.html
class Note:

  NOTES = ['c','c#','d','d#','e','f','f#','g','g#','a','a#','b']

  def __init__(self, note, octave=4):
    self.octave = octave
    if isinstance(note, int):
      self.index = note
      self.note = Note.NOTES[note]
    elif isinstance(note, str):
      self.note = note.strip().lower()
      self.index = Note.NOTES.index(self.note)

  def transpose(self, halfsteps):
    octave_delta, note = divmod(self.index + halfsteps, 12)
    return Note(note, self.octave + octave_delta)

  def frequency(self):
    base_frequency = 16.35159783128741 * 2.0 ** (float(self.index) / 12.0)
    return base_frequency * (2.0 ** self.octave)

  def __float__(self):
    return self.frequency()


class Scale:

  def __init__(self, root, intervals):
    self.root = Note(root.index, 0)
    self.intervals = intervals

  def get(self, index):
    intervals = self.intervals
    if index < 0:
      index = abs(index)
      intervals = reversed(self.intervals)
    intervals = itertools.cycle(self.intervals)
    note = self.root
    for i in range(index):
      note = note.transpose(next(intervals))
    return note

  def index(self, note):
    intervals = itertools.cycle(self.intervals)
    index = 0
    x = self.root
    while x.octave != note.octave or x.note != note.note:
      x = x.transpose(next(intervals))
      index += 1
    return index

  def transpose(self, note, interval):
    return self.get(self.index(note) + interval)


def sine(frequency, length, rate):
  length = int(length * rate)
  factor = float(frequency) * (math.pi * 2) / rate
  return numpy.sin(numpy.arange(length) * factor)

def shape(data, points, kind='slinear'):
    items = points.items()
    sorted(items,key=itemgetter(0))
    keys = list(map(itemgetter(0), items))
    vals = list(map(itemgetter(1), items))
    interp = interpolate.interp1d(keys, vals, kind=kind)
    factor = 1.0 / len(data)
    shape = interp(numpy.arange(len(data)) * factor)
    return data * shape

def harmonics1(freq, length):
  a = sine(freq * 1.00, length, 44100)
  b = sine(freq * 2.00, length, 44100) * 0.5
  c = sine(freq * 4.00, length, 44100) * 0.125
  return (a + b + c) * 0.2

def harmonics2(freq, length):
  a = sine(freq * 1.00, length, 44100)
  b = sine(freq * 2.00, length, 44100) * 0.5
  return (a + b) * 0.2

def pluck1(note):
  chunk = harmonics1(note.frequency(), 0.4)
  return shape(chunk, {0.0: 0.0, 0.005: 1.0, 0.25: 0.2, 0.9: 0.1, 1.0:0.0})

def pluck2(note):
  chunk = harmonics2(note.frequency(), 0.8)
  return shape(chunk, {0.0: 0.0, 0.5:0.75, 0.8:0.4, 1.0:0.1})

def chord(n, scale):
  root = scale.get(n)
  third = scale.transpose(root, 2)
  fifth = scale.transpose(root, 4)
  return pluck1(root) + pluck1(third) + pluck1(fifth)

### LAINATTU KOODI LOPPUU ###

# Allaoleva metodi luo populaatiolle generaation 1 vanhemmat
# parametrit num, num1 = vanhempien määrä, nuottien määrä
# Laittaa nuotit listaan ja laittaa listan toiseen listaan, jossa kaikki vanhemmat
def createParents(num, num1):
    a = 0
    allparents = []
    while a < num:
        beats = 1
        notes = beats * num1
        choose = [28, 29, 30, 31, 32, 33, 34, 35] #a-mollin nuotit
        chosen = []
        for i in range(notes):
            chosen.append(random.choice(choose))
        allparents.append(chosen)
        a += 1
    return allparents

# Metodi luo nuotit, jota lainattu soitto-ohjelma ymmärtää
# parametrit population, note = luotu populaatio, nuottiavain
def createNotes(population, note):
    root = Note(note, 3)
    scale = Scale(root, [2, 1, 2, 2, 1, 2, 2]) #mollin nuottien stepit
    chunk = []
    for i in range(len(population)):
        chunks = []
        for j in range(len(population[i])):
            chunks.append(pluck1(scale.get(population[i][j])))
        chunk.append(chunks)
    return chunk

# Metodi soittaa kaikki tehdyt "kappaleet"
# parametrit chunk, population, id = luodut nuotit, luotu populaatio, generaation id-numero
def playMusic(chunk, population, id):
    print("Generaation", id + 1, "melodiat")
    fitgiven = [] #arvosanoille oma lista, joka liitetään vanhemman nuottien perään
    for i in range(len(chunk)):
        print("Melodia", i + 1)

        #soittaa melodiat
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paFloat32, channels=1, rate=44100, output=1)
        stream.write(numpy.concatenate(chunk[i]).astype(numpy.float32).tobytes())
        stream.close()
        p.terminate()

        #arvosanojen antaminen
        while True:
            try:
                fitness = int(input("Anna arvosana (0-10): "))
                if fitness >= 0 and fitness <= 10:
                    break
                else:
                    print("Anna arvosana uudestaan.")
            except ValueError:
                print("Arvosana ei ollut luku.")
                continue
        population[i].append([fitness])
        fitgiven.append(population[i])
    return fitgiven

# Metodi, jolla voi viedä nuotit ulos ohjelmasta midi-nuotteina(harrastan konemusiikin tekemistä
# joten tämä itselle tärkeä ominaisuus)
# parametrit notes, id = luotu populaatio, generaation id-numero
def exportMidi(notes, id):
    degrees = []
    for i in range(len(notes)):
        if notes[i] == 28:
            notes[i] = 69
        elif notes[i] == 29:
            notes[i] = 71
        elif notes[i] == 30:
            notes[i] = 72
        elif notes[i] == 31:
            notes[i] = 74
        elif notes[i] == 32:
            notes[i] = 76
        elif notes[i] == 33:
            notes[i] = 77
        elif notes[i] == 34:
            notes[i] = 79
        elif notes[i] == 35:
            notes[i] = 81
        degrees.append(notes[i]) # MIDI note number 69 on A
    track = 0
    channel = 0
    time = 0 # In beats
    duration = 1 # In beats
    tempo = 119 # In BPM
    volume = 100 # 0-127
    MyMIDI = MIDIFile(1) # One track, defaults to format 1 (tempo track automatically created)
    MyMIDI.addTempo(track,time, tempo)

    for pitch in degrees:
        MyMIDI.addNote(track, channel, pitch, time, duration, volume)
        time = time + 1

    file = open("melody" + str(id) + ".mid", "wb") #tallentaa id:n mukaan, jotta voi tallentaa monta melodiaa
    MyMIDI.writeFile(file)


# pääohjelman metodi
def main():

    print("Anna parillinen määrä ensimmäisen genaraation melodioita.")
    while True:
        try:
            num = int(input("Kuinka monta ensimmäisen generaation melodiaa(minimi 4): "))
            if num >= 4 and num % 2 == 0:
                break
            else:
                print("Anna määrä uudestaan")
        except ValueError:
            print("Määrä ei ollut luku")
            continue
    
    #tällä hetkellä toimii vain a-mollissa. Jatkokehityksessä toiminnallisuus duuriin
    #ja molliin sekä mihin vaan nuottiavaimeen
    note = "a" 
    num1 = int(input("Kuinka monta nuottia: "))

    population = createParents(num, num1) #luodaan 1. generaation vanhemmat
    id = 0

    chunk = createNotes(population, note) #luodaan 1. generaation vanhemmille nuotit


    # while-looppi toistaa soittoa, tallennusta, arviointia, populaation pariutusta, mutaatioita jne.
    # aktiivinen niin pitkään kunnes käyttäjä syöttää kysyttäessä "n"
    active = True
    while active:

        # soitetaan musiikki
        playMusic(chunk, population, id)

        # midi-tallennus
        tallennus = input("tallennetaanko? [y/n] ")
        if tallennus == "y":
            childnumber = int(input("Anna lapsen numero: "))
            exportMidi(population[childnumber - 1][:-1], id)


        #irrotetaan annetut arvosanat stokastiselle ruletille populaatiosta
        #sum-listaan tallennetaan annettut arvosanat
        sum = []
        for i in range(len(population)):
            sum.append(population[i][-1][0])
        sum = numpy.array(sum)

        # stokastiselle ruletille tieto kuinka monta vanhempaa, sekä kuinka moni heistä pääsee
        # ruletti-valintaan (ohjelmassa kaikki pääsevät, jotta populaatio ei kutistu)
        n = num
        sample_size = num

        # randominumero ruletille
        rng = default_rng()

        #suoritetaan ruletti
        print('Stokastinen ruletti:')
        selected = sus(rng, population, sum, sample_size)

        #pariutetaan valitut, luodaan isit ja äidit
        m, d = selectedToPairs(selected, population)
        children = []
        for i in range(len(m)):
            if len(m) == len(d):
                #valitut tekevät lapset (94% todennäköisyyydellä pariutuvat)
                children += (crossover(m[i], d[i]))

        #hieman mutaatiota (montaa erilaista matalilla todennäköisyyksillä)
        population = mutation(children)

        #lisätään randomi geeni geenipoolista (2% todennäköisyydellä)
        population = addRandomGene(population)
        print("Uusi sukupolvi: ")
        print(population)

        active = input("jatketaanko? [y/n] ") != "n"

        #luodaan nuotit n:nnelle generaatiolle
        chunk = createNotes(population, note)

        #lisätään id:seen 1 niin seuraavalla kierroksella on seuraavan generaation id
        id += 1

if __name__ == '__main__':
    main()







