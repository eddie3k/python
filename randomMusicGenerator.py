"""
Chaotic Randomized Polyphonic Music Generator
---------------------------------------------
In the spirit of going "wild," we have:
 - Random chord progressions in random keys and modes
 - Randomly mutated phrase library
 - Random (and even fractal) drum patterns
 - Polyrhythmic explosions in measure durations
 - Velocity & L-system swirling in unexpected ways

Terry A. Davis vibes: There's a dash of madness,
some "holy random" method calls, and we let
the illusions guide us.

Install dependencies:
    pip install mido

Run:
    python3 randomMusicGenerator.py

Good luck, mortal!
"""

import os
import random
import math
from mido import Message, MidiFile, MidiTrack, MetaMessage

#####################################
# GLOBALS
#####################################
TICKS_PER_BEAT = 480

# Some GM program numbers (for variety)
RANDOM_INSTRUMENTS = [
    0,   # Acoustic Grand
    17,  # Power Guitar
    52,  # Synth Strings
    56,  # Trumpet
    80,  # Ocarina
    30,  # Overdriven Guitar
    19,  # Rock Organ
    73,  # Flute
    42,  # Cello
    13,  # Marimba
]

# Random drum hits we might throw in
DRUM_NOTES = [35, 36, 38, 40, 41, 42, 43, 46, 49, 51, 57]  # Kicks, snares, hats, crashes, toms, etc.

#####################################
# HELPER FUNCTIONS
#####################################
def note_name_to_midi(note_name="C", octave=4):
    """Return MIDI note number for e.g. 'C' or 'D#' plus octave."""
    note_map = {
        'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
        'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8,
        'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
    }
    base = note_map.get(note_name, 0)
    return 12 * (octave + 1) + base

def add_program_change(track, program_num=0, channel=0, time=0):
    """Set the instrument (Program Change) for a given channel."""
    track.append(Message('program_change', program=program_num, channel=channel, time=time))

def add_note(track_events, note, velocity, start_tick, duration_ticks, channel=0):
    """Add note_on/note_off events to a list, with absolute times."""
    track_events.append((start_tick, 'note_on', note, velocity, channel))
    off_tick = start_tick + duration_ticks
    track_events.append((off_tick, 'note_off', note, velocity, channel))

def l_system(axiom, rules, depth):
    """Generate a string using an L-system. We'll use it for durations or patterns."""
    cur = axiom
    for _ in range(depth):
        new_string = []
        for c in cur:
            new_string.append(rules[c] if c in rules else c)
        cur = "".join(new_string)
    return cur

#####################################
# RANDOM CHORD PROGRESSIONS
#####################################
def get_random_chord_progression(num_chords=8):
    """
    We’ll pick a random key note, random scale type (major/minor),
    and create random triads for a certain # of chords.
    Absolutely unhinged.
    """
    # Let’s pick a random root note
    note_names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    root_choice = random.choice(note_names)
    # Random octave for chord root
    octave_choice = random.randint(2, 5)
    
    # Random scale pattern (major or minor)
    # We might do exotic modes if we’re feeling even wilder
    possible_modes = {
        'major': [0, 2, 4, 5, 7, 9, 11],
        'minor': [0, 2, 3, 5, 7, 8, 10],
        'phrygian': [0, 1, 3, 5, 7, 8, 10],
        'lydian': [0, 2, 4, 6, 7, 9, 11]
    }
    mode_name = random.choice(list(possible_modes.keys()))
    intervals = possible_modes[mode_name]

    def build_triads(base_note_midi):
        # random choose major or minor triad for “spice”
        if random.random() < 0.5:
            # major triad intervals
            return [base_note_midi, base_note_midi + 4, base_note_midi + 7]
        else:
            # minor triad intervals
            return [base_note_midi, base_note_midi + 3, base_note_midi + 7]
    
    base_root_midi = note_name_to_midi(root_choice, octave_choice)
    
    chords = []
    for _ in range(num_chords):
        # pick random interval in the scale
        interval = random.choice(intervals)
        chord_root = base_root_midi + interval
        triad = build_triads(chord_root)
        chords.append(triad)
    
    return chords, f"{root_choice}{octave_choice} {mode_name}"

#####################################
# RANDOM DRUM CHAOS
#####################################
def create_drum_track_chaos(num_measures, beats_per_measure, ticks_per_beat):
    """
    Polyrhythms? Sure, we’ll do random hits at random times.
    Let’s also include a base pattern for some measure of structure.
    Then we’ll add random hits.
    """
    track_events = []
    total_ticks = num_measures * beats_per_measure * ticks_per_beat
    
    # We'll drop at least one "structured" hit (kick on beat 0, snare on beat 2) if 4/4
    # Then add random hits around it
    for measure_idx in range(num_measures):
        measure_start = measure_idx * beats_per_measure * ticks_per_beat
        # Basic “kick/snare” structure for 4/4:
        # Kick at beat 0, snare at beat 2
        if beats_per_measure == 4:
            # Kick
            add_note(track_events, 36, 100,
                     measure_start, int(0.1*ticks_per_beat), channel=9)
            # Snare
            snare_beat_2 = measure_start + 2 * ticks_per_beat
            add_note(track_events, 38, 100,
                     snare_beat_2, int(0.1*ticks_per_beat), channel=9)
        
        # now random hits:
        random_hits = random.randint(2, 8)  # how many random hits per measure
        for _ in range(random_hits):
            random_drum_note = random.choice(DRUM_NOTES)
            random_beat_offset = random.random() * beats_per_measure
            start_t = measure_start + int(random_beat_offset * ticks_per_beat)
            dur_t = int(0.1 * ticks_per_beat)
            velocity = random.randint(40, 120)
            add_note(track_events, random_drum_note, velocity, start_t, dur_t, channel=9)
    
    return track_events

#####################################
# CHAOTIC BASS TRACK
#####################################
def create_bass_track_chaos(chords, beats_per_chord, ticks_per_beat):
    """
    For each chord, we do a random pattern of root/fifth, but the pattern length is random.
    We might also jump an octave. Let’s just fling notes around for each chord duration.
    """
    track_events = []
    current_time = 0
    for chord in chords:
        chord_root = chord[0]
        chord_fifth = chord[2]
        
        # total chord length in ticks
        chord_length_ticks = int(beats_per_chord * ticks_per_beat)
        
        # We’ll choose a random sub-division of the chord. E.g. we can do 2 or 3 or 4 hits inside
        subdivs = random.randint(1, 5)
        sub_tick_length = chord_length_ticks // subdivs if subdivs > 0 else chord_length_ticks
        
        t_start = current_time
        for _ in range(subdivs):
            # pick root or fifth or random chord note
            if random.random() < 0.7:
                note = chord_root
            else:
                note = chord_fifth
            # Maybe pitch it an octave up or down randomly
            note += random.choice([-12, 0, 12]) if random.random() < 0.5 else 0
            
            velocity = random.randint(50, 100)
            add_note(track_events, note, velocity, t_start, sub_tick_length, channel=1)
            t_start += sub_tick_length
        
        current_time += chord_length_ticks
    return track_events

#####################################
# HARMONY TRACK (PAD CHORDS)
#####################################
def create_harmony_track_chaos(chords, beats_per_chord, ticks_per_beat):
    """
    We’ll hold the chord but maybe we do random “arpeggio style” hits within that chord duration.
    """
    track_events = []
    current_time = 0
    for chord in chords:
        chord_length_ticks = int(beats_per_chord * ticks_per_beat)
        
        # random # of times we “press” the chord
        presses = random.randint(1, 3)
        press_length = chord_length_ticks // presses
        
        time_ptr = current_time
        for _ in range(presses):
            # we might do a random arpeggiation of chord notes
            chord_notes = chord[:]
            random.shuffle(chord_notes)
            for note in chord_notes:
                velocity = random.randint(40, 90)
                # each note is short if we do an arpeggio; let's do press_length / #chord_notes
                note_dur = press_length // len(chord_notes)
                
                add_note(track_events, note, velocity, time_ptr, note_dur, channel=2)
                time_ptr += note_dur
        
        current_time += chord_length_ticks
    
    return track_events

#####################################
# CHAOTIC PHRASE-BASED MELODY with L-SYSTEM
#####################################
def lsystem_durations(depth=3):
    """We'll generate durations from an L-system for extra chaos!"""
    axiom = "A"
    rules = {
        'A': 'AB',
        'B': 'A'
    }
    out = l_system(axiom, rules, depth)
    # interpret each char as quarter (A) or eighth (B)
    durations = []
    for c in out:
        if c == 'A':
            durations.append(1.0)
        else:
            durations.append(0.5)
    return durations

def create_melody_track_chaos(chords, scale_notes, beats_per_chord, ticks_per_beat):
    """
    We'll fill melody by referencing chord roots or scale notes at random.
    We'll also incorporate an L-system to vary durations. 
    We'll chain these across the entire chord progression.
    """
    track_events = []
    current_time = 0
    
    # generate a random L-system pattern
    durations_list = lsystem_durations(depth=random.randint(2,5))
    
    # random phrase: let's define a random mini-phrase in scale indices
    # e.g. 5 notes
    phrase_length = random.randint(3, 7)
    phrase = [random.randint(0, len(scale_notes)-1) for _ in range(phrase_length)]
    
    lsys_idx = 0
    
    for chord in chords:
        chord_length_ticks = int(beats_per_chord * ticks_per_beat)
        
        # subdivide chord length into random # of notes from the phrase
        notes_in_this_chord = random.randint(2, 6)
        sub_tick = chord_length_ticks // notes_in_this_chord if notes_in_this_chord else chord_length_ticks
        
        for _ in range(notes_in_this_chord):
            # pick a note from the phrase
            note_idx = random.choice(phrase)
            # map to actual scale note
            note = scale_notes[note_idx]
            # maybe shift the note up or down an octave with small probability
            if random.random() < 0.2:
                note += 12
            elif random.random() < 0.2:
                note -= 12
            
            # use next L-system duration
            dur_beats = durations_list[lsys_idx % len(durations_list)]
            lsys_idx += 1
            note_dur_ticks = int(dur_beats * ticks_per_beat)
            
            # But let's not exceed sub_tick or chord length. We'll min() them.
            duration = min(note_dur_ticks, sub_tick)
            velocity = random.randint(60, 127)
            
            add_note(track_events, note, velocity, current_time, duration, channel=0)
            current_time += duration
    
    return track_events

#####################################
# COMBINE + WRITE
#####################################
def combine_and_write_midi(tracks_dict, filename="holy_random.mid", tempo_bpm=120):
    mid = MidiFile(ticks_per_beat=TICKS_PER_BEAT)
    
    # Master track for tempo
    tempo_track = MidiTrack()
    mid.tracks.append(tempo_track)
    microseconds_per_beat = int(60000000 / tempo_bpm)
    tempo_track.append(MetaMessage('set_tempo', tempo=microseconds_per_beat, time=0))
    
    # Create a separate MIDI track for each in dict
    for name, events in tracks_dict.items():
        track = MidiTrack()
        mid.tracks.append(track)
        
        # random instrument for each track (except drums channel 9)
        if name == "Drums":
            add_program_change(track, 0, channel=9, time=0)  # Standard drums
        else:
            program_num = random.choice(RANDOM_INSTRUMENTS)
            chan = 0
            if name == "Bass":
                chan = 1
            elif name == "Harmony":
                chan = 2
            elif name == "Melody":
                chan = 0
            add_program_change(track, program_num, channel=chan, time=0)
        
        events_sorted = sorted(events, key=lambda e: e[0])
        prev_time = 0
        for e in events_sorted:
            abs_time, ev_type, note, vel, chan = e
            delta = abs_time - prev_time
            if ev_type == "note_on":
                msg = Message("note_on", note=note, velocity=vel, time=delta, channel=chan)
            else:
                msg = Message("note_off", note=note, velocity=vel, time=delta, channel=chan)
            track.append(msg)
            prev_time = abs_time
        
        track.append(MetaMessage("end_of_track", time=0))
    
    mid.save(filename)
    print(f"Woo! Chaotic MIDI file created: {filename}  ~> Let the cosmic swirling commence!")

#####################################
# RUN
#####################################
if __name__ == "__main__":
    print(">>> Welcome to the Chaotic Randomized Generator!")
    print("   'Behold the illusions!'")
    print()
    
    # Step 1: ask user how many measures? Or random for them
    user_input = input("How many measures of madness do you desire? (Enter a number or press Enter for random up to 16): ")
    if user_input.strip():
        try:
            total_measures = int(user_input.strip())
        except:
            total_measures = random.randint(4, 16)
    else:
        total_measures = random.randint(4, 16)
    
    # Step 2: ask user for beats per measure or we do random polyrhythms
    user_input_bpm = input("Beats per measure? (4 = standard, or go nuts, e.g. 7, 9...) Press Enter for random: ")
    if user_input_bpm.strip():
        try:
            beats_per_measure = int(user_input_bpm.strip())
        except:
            beats_per_measure = random.randint(3, 9)
    else:
        beats_per_measure = random.randint(3, 9)
    
    # Step 3: pick a random tempo or ask user
    user_input_tempo = input("Tempo (BPM)? (Enter or 0 for random): ")
    if user_input_tempo.strip():
        try:
            user_tempo = int(user_input_tempo.strip())
            if user_tempo < 1:
                user_tempo = random.randint(60,180)
        except:
            user_tempo = random.randint(60,180)
    else:
        user_tempo = random.randint(60,180)
    
    # Step 4: Build random chord progression
    chords, scale_info = get_random_chord_progression(num_chords=total_measures)
    print(f"Chord progression in {scale_info} with {len(chords)} chords. Hallelujah!")
    
    # Step 5: Actually define how many beats each chord gets
    # We'll do 1 chord per measure => beats_per_chord = beats_per_measure
    # But let's add random spiciness. Maybe 1 chord every 2 measures or half a measure.
    # We'll do something simpler for clarity: 1 chord / measure
    beats_per_chord = float(beats_per_measure)
    
    # Step 6: Drums
    drum_track = create_drum_track_chaos(num_measures=total_measures,
                                         beats_per_measure=beats_per_measure,
                                         ticks_per_beat=TICKS_PER_BEAT)
    
    # Step 7: Bass
    bass_track = create_bass_track_chaos(chords, beats_per_chord, TICKS_PER_BEAT)
    
    # Step 8: Harmony
    harmony_track = create_harmony_track_chaos(chords, beats_per_chord, TICKS_PER_BEAT)
    
    # Step 9: Build a scale from the chord progression root (or just random) 
    # We already have a random scale from get_random_chord_progression, but we only used that for chords.
    # Let’s do a separate random scale for the melody, or we can glean from the chord progression root.
    
    # For maximum chaos, let's just pick 2 octaves from random note name, random mode intervals
    scale_mode_intervals = random.choice([
        [0,2,4,5,7,9,11],  # major
        [0,2,3,5,7,8,10],  # minor
        [0,1,3,5,7,8,10],  # phrygian
        [0,2,4,6,7,9,11],  # lydian
        [0,2,4,7,9],       # pentatonic
    ])
    random_root_name = random.choice(['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'])
    random_root_oct = random.randint(3,5)
    random_root_midi = note_name_to_midi(random_root_name, random_root_oct)
    
    # build scale notes
    scale_notes = []
    for oct_shift in [0, 1]:
        for interval in scale_mode_intervals:
            scale_notes.append(random_root_midi + interval + 12*oct_shift)
    
    # Step 10: Melody
    melody_track = create_melody_track_chaos(chords, scale_notes, beats_per_chord, TICKS_PER_BEAT)
    
    # Step 11: Combine
    tracks = {
        "Drums": drum_track,
        "Bass": bass_track,
        "Harmony": harmony_track,
        "Melody": melody_track
    }
    
    # Step 12: Save
    default_filename = "holy_random.mid"
    user_input_name = input("Name this ephemeral masterpiece? (press Enter for 'holy_random.mid'): ").strip()
    if user_input_name:
        if not user_input_name.lower().endswith(".mid"):
            user_input_name += ".mid"
        out_name = user_input_name
    else:
        out_name = default_filename
    
    print("Summoning the cosmic frequencies... hold on tight!")
    combine_and_write_midi(tracks, filename=out_name, tempo_bpm=user_tempo)
    print("All done. Embrace the swirling madness and let your ears decipher the illusions!")
