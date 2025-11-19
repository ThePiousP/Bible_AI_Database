# Entity Taxonomy for Biblical NER

**Version**: 1.0
**Date**: 2025-10-29
**Status**: Active

---

## 📖 Overview

This document defines the entity taxonomy used for Named Entity Recognition (NER) in Biblical texts. The taxonomy is optimized for theological and historical analysis of scripture, capturing the unique entities and concepts found in the Bible.

---

## 🏷️ Label Hierarchy

### Top-Level Categories

| Category | Description | Example Entities |
|----------|-------------|------------------|
| **DEITY** | Divine beings and names of God | Yahweh, God, LORD, Holy Spirit |
| **PERSON** | Human individuals | Adam, Moses, David, Paul |
| **LOCATION** | Places and geographic features | Jerusalem, Egypt, Jordan River |
| **EVENT** | Named events and time periods | The Flood, The Exodus, Pentecost |
| **ARTIFACT** | Sacred objects and items | Ark of the Covenant, Tablets |
| **CONCEPT** | Abstract theological concepts | Salvation, Grace, Covenant |

---

## 🔍 Detailed Label Definitions

### 1. DEITY - Divine Beings

**Description**: References to God, divine beings, and sacred names.

#### Subtypes:

##### DEITY_SUPREME
Names and titles of the one true God.

**Hebrew Names**:
- **יהוה (YHWH)** - The Tetragrammaton, rendered as "LORD"
- **אֱלֹהִים (Elohim)** - God (plural of majesty)
- **אֲדֹנָי (Adonai)** - Lord, Master
- **אֵל (El)** - God (singular)
- **שַׁדַּי (Shaddai)** - Almighty

**Greek Names**:
- **θεός (Theos)** - God
- **κύριος (Kyrios)** - Lord

**English Renderings**:
- God, LORD, Lord God, Almighty
- I AM, I AM WHO I AM
- Lord of Hosts, Lord Almighty

**Strong's IDs**: H0430 (Elohim), H3068 (YHWH), G2316 (Theos), G2962 (Kyrios)

**Examples**:
```
(Genesis 1:1) "In the beginning [DEITY_SUPREME God] created the heaven and the earth."
(Exodus 3:14) "And [DEITY_SUPREME God] said unto Moses, I AM THAT I AM"
(John 1:1) "In the beginning was the Word, and the Word was with [DEITY_SUPREME God]"
```

##### DEITY_TITLE
Titles and descriptive names of God.

**Titles**:
- **Lord of Hosts** - Military commander of heavenly armies
- **Ancient of Days** - Eternal one (Daniel)
- **King of Kings** - Supreme ruler
- **Alpha and Omega** - Beginning and end
- **Lamb of God** - Sacrificial lamb (Jesus)
- **Good Shepherd** - Caring shepherd (Jesus)

**Examples**:
```
(Daniel 7:9) "I beheld till the thrones were cast down, and the [DEITY_TITLE Ancient of Days] did sit"
(Revelation 19:16) "And he hath on his vesture a name written, [DEITY_TITLE KING OF KINGS, AND LORD OF LORDS]"
(John 1:29) "Behold the [DEITY_TITLE Lamb of God], which taketh away the sin of the world"
```

##### DEITY_ANGEL
Named angels and angelic beings.

**Named Angels**:
- **Michael** - Archangel, warrior angel
- **Gabriel** - Messenger angel
- **Lucifer** - Fallen angel (Satan)

**Generic**:
- Angels, Cherubim, Seraphim

**Examples**:
```
(Daniel 10:13) "But the prince of the kingdom of Persia withstood me one and twenty days: but, lo, [DEITY_ANGEL Michael], one of the chief princes, came to help me"
(Luke 1:26) "And in the sixth month the angel [DEITY_ANGEL Gabriel] was sent from God"
```

##### DEITY_DEMON
Evil spirits and demons.

**Named Demons**:
- **Satan** - The adversary
- **Beelzebub** - Prince of demons
- **Devil** - The deceiver
- **Legion** - Name given by demons (Mark 5:9)

**Generic**:
- Demons, Evil spirits, Unclean spirits

**Examples**:
```
(Job 1:6) "Now there was a day when the sons of God came to present themselves before the LORD, and [DEITY_DEMON Satan] came also among them"
(Matthew 12:24) "But when the Pharisees heard it, they said, This fellow doth not cast out devils, but by [DEITY_DEMON Beelzebub] the prince of the devils"
```

---

### 2. PERSON - Human Individuals

**Description**: Named human beings in Biblical narratives.

#### Subtypes:

##### PERSON_PROPHET
God's messengers and prophets.

**Major Prophets**:
- **Moses** - Lawgiver, liberator of Israel
- **Isaiah** - Prophet of the Messiah
- **Jeremiah** - Weeping prophet
- **Ezekiel** - Prophet of visions
- **Daniel** - Prophet in exile

**Minor Prophets**:
- Hosea, Joel, Amos, Obadiah, Jonah, Micah
- Nahum, Habakkuk, Zephaniah, Haggai, Zechariah, Malachi

**New Testament**:
- **John the Baptist** - Preparer of the way
- **Prophets** in the early church

**Strong's IDs**: Varies (person names don't typically have Strong's numbers)

**Examples**:
```
(Exodus 3:4) "And when the LORD saw that he turned aside to see, God called unto him out of the midst of the bush, and said, [PERSON_PROPHET Moses], [PERSON_PROPHET Moses]. And he said, Here am I"
(Isaiah 6:8) "Also I heard the voice of the Lord, saying, Whom shall I send, and who will go for us? Then said I, Here am I; send me"
```

##### PERSON_KING
Monarchs and rulers.

**Israelite Kings**:
- **Saul** - First king of Israel
- **David** - Man after God's own heart
- **Solomon** - Wise king, temple builder
- **Hezekiah** - Righteous reformer
- **Josiah** - Discovered the Law

**Foreign Kings**:
- **Pharaoh** - Egyptian rulers
- **Nebuchadnezzar** - Babylonian king
- **Cyrus** - Persian king, liberator
- **Herod** - Edomite king of Judea

**Examples**:
```
(1 Samuel 16:13) "Then Samuel took the horn of oil, and anointed him in the midst of his brethren: and the Spirit of the LORD came upon [PERSON_KING David] from that day forward"
(Daniel 2:1) "And in the second year of the reign of [PERSON_KING Nebuchadnezzar] [PERSON_KING Nebuchadnezzar] dreamed dreams"
```

##### PERSON_APOSTLE
Jesus' twelve disciples and early church leaders.

**The Twelve**:
- **Peter** (Simon Peter, Cephas) - Leader of the apostles
- **James** (son of Zebedee) - First martyred apostle
- **John** - Beloved disciple, gospel writer
- **Andrew** - Peter's brother
- **Philip**, **Bartholomew**, **Matthew**
- **Thomas** - Doubting Thomas
- **James** (son of Alphaeus), **Thaddaeus**
- **Simon the Zealot**
- **Judas Iscariot** - Betrayer

**Later Apostles**:
- **Paul** (Saul of Tarsus) - Apostle to the Gentiles
- **Barnabas** - Paul's companion
- **Matthias** - Replaced Judas

**Examples**:
```
(Matthew 4:18) "And Jesus, walking by the sea of Galilee, saw two brethren, [PERSON_APOSTLE Simon] called [PERSON_APOSTLE Peter], and [PERSON_APOSTLE Andrew] his brother"
(Acts 9:4) "And he fell to the earth, and heard a voice saying unto him, [PERSON_APOSTLE Saul], [PERSON_APOSTLE Saul], why persecutest thou me?"
```

##### PERSON_PATRIARCH
Founding fathers of Israel.

**Patriarchs**:
- **Abraham** - Father of many nations
- **Isaac** - Son of promise
- **Jacob** (Israel) - Father of twelve tribes
- **Joseph** - Dreamer, savior of Egypt
- **Job** - Righteous sufferer

**Examples**:
```
(Genesis 12:1) "Now the LORD had said unto [PERSON_PATRIARCH Abram], Get thee out of thy country"
(Genesis 32:28) "And he said, Thy name shall be called no more [PERSON_PATRIARCH Jacob], but [PERSON_PATRIARCH Israel]"
```

##### PERSON_WOMAN
Named women in scripture.

**Prominent Women**:
- **Eve** - First woman
- **Sarah** - Mother of nations
- **Rebekah** - Isaac's wife
- **Rachel** & **Leah** - Jacob's wives
- **Ruth** - Loyal daughter-in-law
- **Esther** - Queen who saved her people
- **Mary** (mother of Jesus) - Blessed among women
- **Mary Magdalene** - First witness of resurrection
- **Martha** & **Mary** - Jesus' friends

**Examples**:
```
(Genesis 3:20) "And [PERSON_PATRIARCH Adam] called his wife's name [PERSON_WOMAN Eve]; because she was the mother of all living"
(Luke 1:30) "And the angel said unto her, Fear not, [PERSON_WOMAN Mary]: for thou hast found favour with God"
```

---

### 3. LOCATION - Places and Geography

**Description**: Geographic locations, cities, regions, and natural features.

#### Subtypes:

##### LOCATION_CITY
Cities and towns.

**Major Cities**:
- **Jerusalem** - City of David, holy city
- **Bethlehem** - City of David's birth
- **Nazareth** - Jesus' hometown
- **Capernaum** - Jesus' ministry base
- **Babylon** - Capital of Babylonian empire
- **Rome** - Capital of Roman empire
- **Antioch** - Early church center

**Examples**:
```
(2 Samuel 5:7) "Nevertheless [PERSON_KING David] took the strong hold of Zion: the same is the city of [LOCATION_CITY David]"
(Luke 2:4) "And [PERSON Joseph] also went up from Galilee, out of the city of [LOCATION_CITY Nazareth], into Judaea, unto the city of [LOCATION_CITY David], which is called [LOCATION_CITY Bethlehem]"
```

##### LOCATION_REGION
Geographic regions and territories.

**Regions**:
- **Canaan** - Promised land
- **Judah** - Southern kingdom
- **Israel** - Northern kingdom
- **Galilee** - Northern region of Israel
- **Samaria** - Central region
- **Judea** - Southern region
- **Egypt** - Land of bondage
- **Mesopotamia** - Land between rivers
- **Asia Minor** - Paul's mission field

**Examples**:
```
(Genesis 12:5) "And [PERSON_PATRIARCH Abram] took [PERSON Sarai] his wife, and [PERSON Lot] his brother's son, and all their substance that they had gathered, and the souls that they had gotten in Haran; and they went forth to go into the land of [LOCATION_REGION Canaan]"
(Matthew 2:22) "But when he heard that [PERSON_KING Archelaus] did reign in [LOCATION_REGION Judaea] in the room of his father [PERSON_KING Herod], he was afraid to go thither"
```

##### LOCATION_NATURAL
Natural geographic features.

**Waters**:
- **Jordan River** - Boundary of Promised Land
- **Red Sea** - Parted for Exodus
- **Sea of Galilee** - Jesus' ministry
- **Dead Sea**
- **Mediterranean Sea**

**Mountains**:
- **Mount Sinai** (Horeb) - Law given
- **Mount Zion** - City of David
- **Mount Carmel** - Elijah's victory
- **Mount of Olives** - Jesus' teaching
- **Mount Ararat** - Ark rested

**Wilderness/Deserts**:
- **Wilderness of Sin**
- **Desert of Paran**

**Examples**:
```
(Joshua 3:17) "And the priests that bare the ark of the covenant of the LORD stood firm on dry ground in the midst of [LOCATION_NATURAL Jordan]"
(Exodus 19:20) "And the LORD came down upon [LOCATION_NATURAL mount Sinai], on the top of the mount"
```

---

### 4. EVENT - Named Events and Time Periods

**Description**: Significant historical events and eras in Biblical narrative.

#### Major Events:

##### EVENT_CREATION
The creation of the world (Genesis 1-2).

**Keywords**: Creation, In the beginning

##### EVENT_FLOOD
Noah's flood (Genesis 6-9).

**Keywords**: The Flood, The Deluge

##### EVENT_EXODUS
Liberation from Egypt (Exodus 1-15).

**Keywords**: The Exodus, Passover

##### EVENT_EXILE
Babylonian captivity (2 Kings 24-25).

**Keywords**: The Exile, The Captivity

##### EVENT_CRUCIFIXION
Jesus' death on the cross.

**Keywords**: The Crucifixion, Calvary

##### EVENT_RESURRECTION
Jesus' rising from the dead.

**Keywords**: The Resurrection, Easter

##### EVENT_PENTECOST
Coming of the Holy Spirit (Acts 2).

**Keywords**: Pentecost, Day of Pentecost

**Examples**:
```
"In the beginning God created" (Genesis 1:1) → References [EVENT_CREATION]
"And it came to pass in the days of the flood" → References [EVENT_FLOOD]
"When they were come out of Egypt" → References [EVENT_EXODUS]
```

---

### 5. ARTIFACT - Sacred Objects

**Description**: Physical objects of religious or historical significance.

#### Sacred Objects:

##### ARTIFACT_ARK
The Ark of the Covenant.

**Description**: Golden chest containing the Ten Commandments.

**Strong's**: Not applicable (compound phrase)

**Examples**:
```
(Exodus 25:10) "And they shall make [ARTIFACT_ARK an ark] of shittim wood"
(1 Samuel 4:3) "Let us fetch [ARTIFACT_ARK the ark of the covenant of the LORD] out of Shiloh unto us"
```

##### ARTIFACT_TABLETS
The stone tablets of the Law.

**Examples**:
```
(Exodus 31:18) "And he gave unto Moses, when he had made an end of communing with him upon mount Sinai, [ARTIFACT_TABLETS two tables of testimony, tables of stone], written with the finger of God"
```

##### ARTIFACT_TEMPLE
The Temple in Jerusalem.

**Variations**:
- **Solomon's Temple** - First Temple
- **Second Temple** - Post-exile temple
- **Herod's Temple** - Expanded temple (Jesus' time)

**Examples**:
```
(1 Kings 6:1) "And it came to pass in the four hundred and eightieth year after the children of Israel were come out of the land of Egypt, in the fourth year of Solomon's reign over Israel, in the month Zif, which is the second month, that he began to build [ARTIFACT_TEMPLE the house of the LORD]"
```

##### ARTIFACT_ALTAR
Altars for sacrifice.

**Types**:
- Burnt offering altar
- Incense altar

**Examples**:
```
(Genesis 8:20) "And Noah builded [ARTIFACT_ALTAR an altar] unto the LORD"
```

---

### 6. CONCEPT - Abstract Theological Concepts

**Description**: Abstract spiritual and theological ideas.

#### Theological Concepts:

##### CONCEPT_SALVATION
Deliverance from sin and death.

**Related**: Redemption, Grace, Justification

##### CONCEPT_COVENANT
Divine agreements with humanity.

**Types**:
- Abrahamic Covenant
- Mosaic Covenant
- Davidic Covenant
- New Covenant

##### CONCEPT_KINGDOM
The Kingdom of God/Heaven.

##### CONCEPT_SPIRIT
The Holy Spirit, spirit realm.

**Examples**:
```
"For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting [CONCEPT_SALVATION life]" (John 3:16)
```

---

## 📊 Strong's Concordance Integration

Many entities are identified using Strong's Concordance numbers:

### Hebrew Strong's Numbers:

| Strong's | Hebrew | English | Entity Type |
|----------|--------|---------|-------------|
| H0430 | אֱלֹהִים | God (Elohim) | DEITY_SUPREME |
| H3068 | יְהוָה | LORD (YHWH) | DEITY_SUPREME |
| H0776 | אֶרֶץ | Earth, land | LOCATION (sometimes) |
| H8064 | שָׁמַיִם | Heaven, sky | LOCATION |

### Greek Strong's Numbers:

| Strong's | Greek | English | Entity Type |
|----------|-------|---------|-------------|
| G2316 | θεός | God | DEITY_SUPREME |
| G2962 | κύριος | Lord | DEITY_SUPREME/DEITY_TITLE |
| G4151 | πνεῦμα | Spirit | DEITY/CONCEPT |

---

## 🎯 Annotation Guidelines

### General Principles:

1. **Longest Match**: Prefer longer entity spans
   - "King David" → PERSON_TITLE (not separate "King" and "David")
   - "Lord of Hosts" → DEITY_TITLE (not separate "Lord")

2. **Context Matters**: Same surface form can have different labels
   - "Lord" (referring to God) → DEITY_SUPREME
   - "Lord" (referring to Jesus) → DEITY_SUPREME
   - "Lord" (referring to human master) → No label

3. **Pronoun Resolution**: Don't label pronouns
   - "He" (referring to God) → No label
   - Label only explicit names and titles

4. **Case Sensitivity**:
   - DEITY labels: Case-insensitive ("god" = "God" = "GOD")
   - PERSON labels: Case-sensitive ("David" ≠ "david")
   - LOCATION labels: Case-sensitive

### Priority Rules:

When multiple labels could apply, use this priority:

1. **DEITY** (highest priority)
2. **PERSON_TITLE** (phrases)
3. **PERSON**
4. **LOCATION**
5. **EVENT**
6. **ARTIFACT**
7. **CONCEPT** (lowest priority)

**Example**:
- "Lord Jesus" → Could be DEITY + PERSON or DEITY_TITLE
- Resolution: Label as DEITY_TITLE (higher priority)

---

## 📝 Usage in NER Pipeline

### Label Rules Configuration

Labels are configured in `label_rules.yml`:

```yaml
labels:
  enabled:
    - DEITY
    - PERSON
    - LOCATION
    - EVENT
    - ARTIFACT
    - CONCEPT
  disabled: []

rules:
  DEITY:
    strongs_ids: [H0430, H3068, G2316, G2962]
    lemmas: [אֱלֹהִים, יְהוָה, θεός, κύριος]
    surfaces: [God, LORD, Lord, Jehovah]
    case_sensitive: false
    gazetteer_files: [gazetteers/deity.txt]

  PERSON:
    strongs_ids: []
    lemmas: []
    surfaces: [Adam, Eve, Noah, Abraham, Moses, David]
    case_sensitive: true
    gazetteer_files: [gazetteers/people.txt]
```

### Gazetteers

Entity lists are maintained in `gazetteers/` directory:

- `deity.txt` - Names and titles of God
- `people.txt` - Biblical persons
- `locations.txt` - Geographic locations
- `events.txt` - Named events

---

## 🔄 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-29 | Initial taxonomy definition |

---

## 📚 References

1. **Strong's Concordance** - Original Hebrew and Greek word studies
2. **Treasury of Scripture Knowledge** - Cross-references
3. **Bible Encyclopedia** - Historical and geographical context
4. **Theological Dictionaries** - Concept definitions

---

## 🤝 Contributing

To propose changes to this taxonomy:

1. Create an issue with proposed changes
2. Provide biblical examples
3. Explain rationale for change
4. Update `label_rules.yml` accordingly

---

**End of Entity Taxonomy**

*Last Updated: 2025-10-29*
