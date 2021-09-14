import spacy
import time


nlp = spacy.load('en_core_web_md')  # make sure to use larger package!
start_time = time.time()
doc1 = nlp("travel")
print(doc1.vector)
maxDistance = 0

syns = ["trip",
        "journey",
        "trips",
        "voyage",
        "displacement",
        "voyages",
        "tourism",
        "tourist",
        "voyager",
        "tour",
        "transport",
        "movement",
        "transportation",
        "displacements",
        "journeys",
        "move",
        "visit",
        "go",
        "tours",
        "ride",
        "carriage"]

# for word in syns:
#     doc2 = nlp(word)
#     # Similarity of two documents
#     distance = doc1.similarity(doc2)
#     if distance > maxDistance:
#         maxDistance = distance
#         closestWord = word
#     print(doc1, "<->", doc2, distance)

# print('Closest word:', closestWord, ' with distance:', maxDistance)
# print('time taken:', time.time() - start_time)
