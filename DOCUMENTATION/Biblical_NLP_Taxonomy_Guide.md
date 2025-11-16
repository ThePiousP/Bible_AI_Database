# Biblical NLP Taxonomy Guide for Annotations

## Overview

This taxonomy provides a comprehensive framework for annotating biblical texts with 61 distinct entity labels organized into 9 hierarchical categories. The system is designed to capture theological, linguistic, and literary features of Scripture while maintaining precision through Strong's Concordance integration and curated gazetteers.

**Core Principles:**
- **Theological Accuracy**: Labels reflect literal-grammatical-historical interpretation
- **Hierarchical Priority**: Specific labels override generic ones during conflict resolution
- **Multi-Source Matching**: Entities identified via Strong's IDs, lemmas, surface forms, and gazetteer files
- **Context Sensitivity**: Some labels are case-sensitive to distinguish proper nouns from common usage

---

## Table of Contents

1. [Hierarchical Category System](#hierarchical-category-system)
2. [Label Definitions by Category](#label-definitions-by-category)
3. [Conflict Resolution Rules](#conflict-resolution-rules)
4. [Annotation Guidelines](#annotation-guidelines)
5. [Quick Reference Index](#quick-reference-index)

---

## Hierarchical Category System

The taxonomy organizes 61 labels into 9 priority levels. When multiple labels could apply to the same span, the label from the highest priority category takes precedence.

### Priority Levels (Highest to Lowest)

1. **Divine & Adversarial Identities** (Most Specific)
2. **Divine Speech & Declarations**
3. **People & Roles**
4. **Nations & Places**
5. **Time, Numbers & Measures**
6. **Concrete Nouns**
7. **Ritual, Law & Cultural Practices**
8. **Theology & Literary/Meta**
9. **Catch-All** (Lowest)

---

## Label Definitions by Category

### CATEGORY 1: Divine & Adversarial Identities

These labels identify divine beings, spiritual entities, and their adversaries. They have the highest priority to ensure theological precision.

#### **DEITY**
- **Definition**: References to the Triune God—Father, Son, Holy Spirit
- **Examples**: God, LORD, Jesus, Holy Ghost
- **Notes**: Anchored by Strong's concordance to maintain precision. The most fundamental label in the taxonomy.
- **Case Sensitive**: Varies by implementation

#### **DIVINE_TITLE**
- **Definition**: Names and titles specifically for God
- **Examples**: Holy One of Israel, Ancient of Days, Alpha and Omega, I AM
- **Priority**: Below DEITY but above human titles
- **Case Sensitive**: False

#### **DIVINE_PRONOUN**
- **Definition**: Pronouns referring to God when God is speaking or being referenced
- **Examples**: "I" (when God speaks), "He" (referring to God), "His" (God's possession)
- **Notes**: Context-dependent; requires determining the antecedent
- **Case Sensitive**: False

#### **PNEUMATOLOGY**
- **Definition**: Specific references to the Holy Spirit and His ministry
- **Examples**: Holy Ghost, Comforter, Spirit of Truth, Paraclete
- **Theological Focus**: Third person of the Trinity
- **Case Sensitive**: False

#### **CHRISTOLOGY**
- **Definition**: Direct references to Christ as Messiah and His person/work
- **Examples**: the Lamb of God, Son of Man, Word made flesh, Emmanuel
- **Theological Focus**: Second person of the Trinity, His offices and nature
- **Case Sensitive**: False

#### **SATANIC_TITLE**
- **Definition**: Titles and names for Satan
- **Examples**: tempter, accuser, adversary, evil one, father of lies
- **Notes**: Distinguished from generic demons
- **Case Sensitive**: False

#### **DEMON**
- **Definition**: Named evil spirits or demonic entities
- **Examples**: Legion, Beelzebub, unclean spirits
- **Notes**: More specific than SPIRITUAL_ENTITY
- **Case Sensitive**: False

#### **FALSE_GOD**
- **Definition**: Pagan gods and idols worshiped by non-Israelites
- **Examples**: Baal, Ashtoreth, Dagon, Molech, Diana
- **Notes**: Distinguished from the true God
- **Case Sensitive**: False

#### **SPIRITUAL_ENTITY**
- **Definition**: Generic spiritual beings (angels, demons, cherubim) not otherwise specified
- **Examples**: angel, cherub, seraph, watcher, ministering spirits
- **Strong's IDs**: H3742 (cherub), H5894 (watcher)
- **Notes**: Catch-all for spiritual beings; specific entities use ANGEL_CHORUS or DEMON
- **Case Sensitive**: False

#### **ANGEL_CHORUS**
- **Definition**: Angelic hosts or heavenly armies referenced collectively
- **Examples**: host of heaven, heavenly host, armies of the Lord
- **Notes**: Collective groups rather than individual angels
- **Case Sensitive**: False

---

### CATEGORY 2: Divine Speech & Declarations

These labels mark God's direct speech acts, commands, and declarations. They rank below divine identities but above human speech.

#### **DIVINE_ACTION**
- **Definition**: Actions explicitly performed by God
- **Examples**: "God created", "the LORD spoke", "He breathed"
- **Notes**: God as the subject performing the action
- **Case Sensitive**: False

#### **DIVINE_COMMAND**
- **Definition**: Direct commands issued by God
- **Examples**: "Thou shalt not eat", "Go forth", "Let there be light"
- **Notes**: Imperative forms from God
- **Case Sensitive**: False

#### **DIVINE_PROMISE**
- **Definition**: Explicit promises made by God
- **Examples**: "I will never leave thee", "I will make of thee a great nation"
- **Notes**: Future-oriented declarations by God
- **Case Sensitive**: False

#### **PROPHECY_FORMULA**
- **Definition**: Standard markers introducing prophetic speech
- **Examples**: "Thus saith the LORD", "The word of the LORD came", "Hear the word of the LORD"
- **Notes**: Formulaic phrases signaling divine revelation
- **Case Sensitive**: False

#### **OATH_FORMULA**
- **Definition**: Sworn vows and oath statements
- **Examples**: "As the LORD lives", "God do so to me", "I swear by myself"
- **Notes**: Can be divine or human oaths
- **Case Sensitive**: False

---

### CATEGORY 3: People & Roles

These labels identify human persons, their roles, and actions. Specific roles override generic categories.

#### **PROPHET**
- **Definition**: Individuals identified as prophets in Scripture
- **Examples**: Isaiah, Jeremiah, Elijah, Elisha, Deborah, Anna
- **Notes**: Curated list from JSON; subset of PERSON but more specific
- **Case Sensitive**: True

#### **PERSON**
- **Definition**: Individual human persons named in Scripture
- **Examples**: Moses, Mary, Abraham, Paul, Peter
- **Notes**: Proper names of biblical characters
- **Case Sensitive**: True

#### **TITLE**
- **Definition**: Human titles, honorifics, and role designations
- **Examples**: king, priest, prophet, brother, servant, apostle, son, daughter
- **Strong's IDs**: H1121/G5207 (son), H1323/G2364 (daughter), H1/G3962 (father)
- **Notes**: Both formal offices and family relationships
- **Case Sensitive**: False

#### **GENEALOGY_REF**
- **Definition**: Terms indicating lineage and descendancy
- **Examples**: "thy seed", "begat", "son of", "generations of"
- **Notes**: Focus on ancestral relationships
- **Case Sensitive**: False

#### **HUMAN_COLLECTIVE**
- **Definition**: Groups of people referenced collectively
- **Examples**: families, tribes, nations, peoples, congregation
- **Notes**: Plural or collective nouns for human groups
- **Case Sensitive**: False

#### **HUMAN_PRONOUN**
- **Definition**: Pronouns referring to human persons
- **Examples**: he, she, they, him, her (when referring to people)
- **Notes**: Requires context to distinguish from divine pronouns
- **Case Sensitive**: False

#### **GENERIC_PRONOUN**
- **Definition**: Non-specific pronouns with unclear or general referents
- **Examples**: it, them, those, these (when not clearly human or divine)
- **Notes**: Lower priority catch-all for ambiguous pronouns
- **Case Sensitive**: False

#### **HUMAN_ACTION**
- **Definition**: Actions performed by humans
- **Examples**: "he said", "she went", "they built"
- **Notes**: Human as subject performing action
- **Case Sensitive**: False

#### **VERB**
- **Definition**: Generic verbs without clear subject type
- **Examples**: told, knew, saw (when subject is ambiguous)
- **Notes**: Lowest priority verb category
- **Case Sensitive**: False

---

### CATEGORY 4: Nations & Places

Geographic and ethnic identifiers.

#### **BIBLE_NATIONS**
- **Definition**: Nations, people groups, or ethnic identities
- **Examples**: the Egyptians, the Philistines, the Israelites, the Romans
- **Notes**: Both ancient and New Testament era nations
- **Case Sensitive**: False

#### **LOCATION**
- **Definition**: Named geographic places and landmarks
- **Examples**: Egypt, Jordan, Nazareth, Jerusalem, Bethlehem, Mount Sinai
- **Notes**: Includes cities, regions, mountains, rivers, seas
- **Case Sensitive**: False

---

### CATEGORY 5: Time, Numbers & Measures

Temporal and quantitative references.

#### **TIME**
- **Definition**: Temporal markers indicating when
- **Examples**: "in the morning", "at that time", "the third day", "in the last days"
- **Strong's IDs**: H3117/G2250 (day), H6256/G2540 (time), H7676 (Sabbath), H6453 (Passover)
- **Notes**: Includes specific times, seasons, and temporal phrases
- **Case Sensitive**: False

#### **NUMERIC_SYMBOLISM**
- **Definition**: Numbers with symbolic or theological significance
- **Examples**: forty days, seven times, twelve tribes, the number of the beast (666)
- **Notes**: Numbers carrying meaning beyond literal quantity
- **Case Sensitive**: False

#### **NUMERIC_MEASURE**
- **Definition**: Units of measurement
- **Examples**: cubits, shekels, talents, ephah, homer, hin
- **Notes**: Ancient measurement units for distance, weight, volume
- **Case Sensitive**: False

#### **NUMBER**
- **Definition**: Literal numeric values without symbolic meaning
- **Examples**: seven, twelve, forty (when used literally)
- **Notes**: Baseline category for all numbers
- **Case Sensitive**: False

#### **TOOLS_MEASUREMENT**
- **Definition**: Instruments and implements used for measuring
- **Examples**: scales, rod, plummet, line, measuring reed
- **Notes**: Physical objects used to measure, not the units themselves
- **Case Sensitive**: False

---

### CATEGORY 6: Concrete Nouns

Physical, tangible objects and substances.

#### **BODY_PART**
- **Definition**: Physical parts of the body
- **Examples**: hand, foot, eye, heart, blood, bone
- **Notes**: Includes both literal and metaphorical usage
- **Case Sensitive**: False

#### **FOOD**
- **Definition**: Edible items mentioned in Scripture
- **Examples**: bread, milk, honey, fish, wine, manna
- **Notes**: Includes provisions and dietary items
- **Case Sensitive**: False

#### **BIBLE_ANIMALS**
- **Definition**: Animals named or referenced in Scripture
- **Examples**: lamb, lion, eagle, serpent, dove, locust
- **Notes**: Both literal and symbolic animal references
- **Case Sensitive**: False

#### **BIBLE_FLORA**
- **Definition**: Plants, trees, and vegetation with biblical significance
- **Examples**: cedar of Lebanon, fig tree, vine, olive tree, lily
- **Notes**: Includes symbolic plant imagery
- **Case Sensitive**: False

#### **OBJECTS_MANMADE**
- **Definition**: Human-crafted objects and structures
- **Examples**: ark, altar, sword, temple, throne, chariot
- **Notes**: Artifacts created by human hands
- **Case Sensitive**: False

#### **OBJECTS_NATURAL**
- **Definition**: Natural objects and phenomena not made by humans
- **Examples**: sea, mountains, dust, wind, fire, cloud
- **Notes**: Elements of the natural world
- **Case Sensitive**: False

#### **ECONOMIC_TERM**
- **Definition**: Terms related to money, trade, and commerce
- **Examples**: silver, wages, debt, tribute, tax, merchandise
- **Notes**: Financial and commercial terminology
- **Case Sensitive**: False

---

### CATEGORY 7: Ritual, Law & Cultural Practices

Religious observances, legal commands, and cultural customs.

#### **RITUAL_PRACTICE**
- **Definition**: Religious rituals and ceremonial practices
- **Examples**: burnt offering, circumcision, baptism, Passover, sacrifice
- **Strong's IDs**: H5930 (burnt offering), H8002 (peace offerings), H817 (guilt offering), H4503 (grain offering), H5262 (drink offering), H8573 (wave offering), G3957 (Passover), G4521 (Sabbath), G4061 (circumcision), G907/908 (baptize/baptism), H6419/8605 (pray/prayer), H6684/6685 (fast), G3522/3521 (fast/fasting)
- **Notes**: Extensive Strong's coverage for sacrificial system and liturgical acts
- **Case Sensitive**: False

#### **LAW_COMMANDMENT**
- **Definition**: Legal commands and prohibitions
- **Examples**: "Thou shalt not kill", "Honor thy father and mother"
- **Notes**: Torah/Law requirements
- **Case Sensitive**: False

#### **LITURGICAL_TERM**
- **Definition**: Terms specific to worship and temple service
- **Examples**: sabbath, sacrifice, offering, holy convocation, sanctuary
- **Notes**: Vocabulary of formal worship
- **Case Sensitive**: False

#### **CULTURAL_PRACTICE**
- **Definition**: Human customs and social practices
- **Examples**: "rent their garments", "put ashes on head", betrothal customs
- **Notes**: Social and cultural behaviors
- **Case Sensitive**: False

#### **COVENANT_TERM**
- **Definition**: Words tied to covenant theology
- **Examples**: everlasting covenant, blood of the covenant, covenant faithfulness
- **Notes**: Covenant relationship vocabulary
- **Case Sensitive**: False

#### **BLESSING_FORMULA**
- **Definition**: Formal blessing statements and benedictions
- **Examples**: "Blessed be Abram", "The LORD bless thee and keep thee"
- **Notes**: Formulaic blessings
- **Case Sensitive**: False

#### **CURSE_FORMULA**
- **Definition**: Formal curses and imprecations
- **Examples**: "Cursed be Canaan", "Cursed is the ground"
- **Notes**: Formulaic curses
- **Case Sensitive**: False

#### **SIN**
- **Definition**: Specific sins named in Scripture
- **Examples**: idolatry, adultery, murder, blasphemy, covetousness
- **Notes**: Catalogued transgressions
- **Case Sensitive**: False

---

### CATEGORY 8: Theology & Literary/Meta

Theological concepts, literary devices, and interpretive markers. These have lower priority to avoid swallowing more specific labels.

#### **SOTERIOLOGY**
- **Definition**: Terms related to salvation
- **Examples**: redeemed, justified, sanctified, atonement, propitiation
- **Notes**: Salvation doctrine vocabulary
- **Case Sensitive**: False

#### **ECCLESIOLOGY**
- **Definition**: References to the church and its nature
- **Examples**: the body of Christ, the bride, living stones, temple of the Holy Ghost
- **Notes**: Church doctrine terminology
- **Case Sensitive**: False

#### **ESCHATOLOGY**
- **Definition**: End-times and prophetic future references
- **Examples**: the last trumpet, day of the Lord, new heaven and new earth
- **Notes**: Future prophecy and judgment
- **Case Sensitive**: False

#### **TYPOLOGY**
- **Definition**: Old Testament types and foreshadows of Christ
- **Examples**: ark (of Noah), Isaac, Joseph, the brazen serpent, Melchizedek
- **Strong's IDs**: H121 (Adam), H5146 (Noah), H4872 (Moses), H4442 (Melchizedek), H7716/G286 (lamb), H727/H8392 (ark), H6453/G3957 (Passover), H4908 (tabernacle), H1964/G3485 (temple), H3130 (Joseph), H1732 (David), H3124 (Jonah), H3290 (Jacob/Israel), H1893 (Abel)
- **Notes**: Recognizes Christ-centered interpretive framework
- **Case Sensitive**: True

#### **THEMES**
- **Definition**: Broad theological themes and motifs
- **Examples**: exile, covenant faithfulness, remnant, kingdom of God
- **Notes**: Overarching theological concepts
- **Case Sensitive**: False

#### **INTERTEXTUAL_REF**
- **Definition**: Explicit cross-references to other Scripture
- **Examples**: "as it is written", "according to the prophet", "fulfilling the word"
- **Notes**: Markers of quotation or allusion
- **Case Sensitive**: False

#### **HERMENEUTIC_KEY**
- **Definition**: Words that signal interpretation or application
- **Examples**: "Therefore", "Behold", "Verily", "It is written"
- **Notes**: Transitional markers indicating meaning
- **Case Sensitive**: False

#### **GENRE_MARKER**
- **Definition**: Textual genre identifiers
- **Examples**: parable, psalm, proverb, lament, oracle
- **Notes**: Literary form indicators
- **Case Sensitive**: False

#### **PARABLE_IMAGE**
- **Definition**: Imagery unique to Jesus' parables
- **Examples**: sower, mustard seed, prodigal son, good Samaritan
- **Notes**: Narrative elements within parables
- **Case Sensitive**: False

#### **METAPHORICAL**
- **Definition**: Figurative imagery and metaphors
- **Examples**: "the Lord is my rock", "I am the vine", "ye are the salt"
- **Notes**: Non-literal symbolic language
- **Case Sensitive**: False

#### **METONYMY**
- **Definition**: One thing standing for another by association
- **Examples**: "the cup" (for suffering), "sword" (for judgment/war), "throne" (for authority)
- **Notes**: Substitution of associated concepts
- **Case Sensitive**: False

#### **CONCEPT**
- **Definition**: Abstract ideas and concepts
- **Examples**: truth, love, fear, faith, grace, righteousness
- **Notes**: Non-physical, philosophical concepts
- **Case Sensitive**: False

#### **TRANSLATION_NOTE**
- **Definition**: Translator glosses and marginal notes
- **Examples**: "margin reads…", "or, [alternative reading]"
- **Notes**: Editorial apparatus
- **Case Sensitive**: False

---

### CATEGORY 9: Catch-All

Final fallback categories with lowest priority.

#### **TOPICAL_NOUNS**
- **Definition**: Subject nouns that are the focus of discourse
- **Examples**: famine, altar, war, temple, sacrifice (when not caught by other categories)
- **Notes**: Content words not fitting elsewhere
- **Case Sensitive**: False

#### **OTHER**
- **Definition**: Generic catch-all for unclassified terms
- **Examples**: it, them (when referent unclear), neutral pronouns
- **Notes**: Lowest priority; use sparingly
- **Case Sensitive**: False

---

## Conflict Resolution Rules

When multiple labels could apply to the same text span, the taxonomy uses a priority-based system to determine which label to assign.

### Priority Hierarchy (Highest to Lowest)

1. **Divine & adversarial identities** (DEITY, DIVINE_TITLE, DIVINE_PRONOUN, SATANIC_TITLE, DEMON, FALSE_GOD, PNEUMATOLOGY, SPIRITUAL_ENTITY, ANGEL_CHORUS)

2. **Divine speech/declarations** (DIVINE_ACTION, DIVINE_COMMAND, DIVINE_PROMISE, OATH_FORMULA, PROPHECY_FORMULA)

3. **People & roles** (PROPHET → PERSON → TITLE → GENEALOGY_REF → HUMAN_COLLECTIVE → HUMAN_PRONOUN → GENERIC_PRONOUN → HUMAN_ACTION → VERB)

4. **Nations & places** (BIBLE_NATIONS, LOCATION)

5. **Time, numbers & measures** (TIME, NUMERIC_SYMBOLISM, NUMERIC_MEASURE, NUMBER, TOOLS_MEASUREMENT)

6. **Concrete nouns** (BODY_PART, FOOD, BIBLE_ANIMALS, BIBLE_FLORA, OBJECTS_MANMADE, OBJECTS_NATURAL, ECONOMIC_TERM)

7. **Ritual/law/covenant/cultural & formulas** (RITUAL_PRACTICE, LAW_COMMANDMENT, LITURGICAL_TERM, CULTURAL_PRACTICE, COVENANT_TERM, BLESSING_FORMULA, CURSE_FORMULA, SIN)

8. **Theology & literary/meta** (CHRISTOLOGY, SOTERIOLOGY, ECCLESIOLOGY, ESCHATOLOGY, TYPOLOGY, THEMES, INTERTEXTUAL_REF, HERMENEUTIC_KEY, GENRE_MARKER, PARABLE_IMAGE, METAPHORICAL, METONYMY, CONCEPT, TRANSLATION_NOTE)

9. **Catch-all** (TOPICAL_NOUNS, OTHER)

### Resolution Examples

**Example 1: "Moses"**
- Could match: PERSON, PROPHET, TYPOLOGY (Moses as type of Christ)
- Resolution: PROPHET (highest priority among the three)

**Example 2: "Passover"**
- Could match: TIME, RITUAL_PRACTICE, TYPOLOGY
- Resolution: TIME (category 5 beats categories 7 and 8)

**Example 3: "the LORD spoke"**
- Could match: DEITY ("the LORD"), DIVINE_ACTION ("spoke")
- Resolution: Both can coexist on different spans, but DEITY has higher priority if overlapping

**Example 4: "son"**
- Could match: TITLE (human role), DIVINE_TITLE (Son of God)
- Resolution: Depends on context; DIVINE_TITLE wins if referring to Christ

**Example 5: "bread"**
- Could match: FOOD, METAPHORICAL (bread of life), PARABLE_IMAGE
- Resolution: FOOD (category 6) beats METAPHORICAL/PARABLE_IMAGE (category 8)

---

## Annotation Guidelines

### General Principles

1. **Theological Accuracy First**: When in doubt, consult Strong's concordance and trusted theological sources (Chuck Smith, Spurgeon, Tozer)

2. **Context is King**: The same word can have different labels depending on context:
   - "lamb" = BIBLE_ANIMALS (literal), TYPOLOGY (sacrifice system), CHRISTOLOGY (Lamb of God)
   - "son" = TITLE (general), DIVINE_TITLE (Son of God), GENEALOGY_REF (son of David)

3. **Span Boundaries**: 
   - Annotate the minimal span that carries the semantic meaning
   - Include articles and modifiers when they're part of a fixed phrase ("the LORD", "Holy Spirit")
   - Exclude surrounding punctuation unless it's part of the entity

4. **Case Sensitivity Matters**:
   - PERSON, PROPHET, and TYPOLOGY are case-sensitive to distinguish proper names
   - Most other labels are case-insensitive

5. **Strong's Integration**:
   - Strong's IDs provide precise lexical anchoring
   - Use Strong's especially for DEITY, RITUAL_PRACTICE, and TYPOLOGY
   - Strong's H-numbers = Hebrew/Aramaic; G-numbers = Greek

6. **Gazetteer Priority**:
   - Curated gazetteer files provide high-confidence matches
   - Gazetteers represent pre-approved terms from your biblical database

### Workflow for Annotators

**Step 1: Initial Pass**
- Read the verse/passage for overall context
- Identify obvious proper nouns (PERSON, LOCATION, BIBLE_NATIONS)
- Mark clear divine references (DEITY, DIVINE_TITLE)

**Step 2: Detailed Analysis**
- Check for ritual/liturgical terms
- Identify theological concepts (SOTERIOLOGY, CHRISTOLOGY, etc.)
- Mark literary devices (METAPHORICAL, TYPOLOGY)

**Step 3: Conflict Resolution**
- Apply priority rules to overlapping spans
- Verify Strong's IDs for ambiguous cases
- Consult gazetteers for confirmation

**Step 4: Quality Check**
- Ensure consistent labeling across similar contexts
- Verify that labels align with literal-grammatical-historical interpretation
- Check that divine pronouns correctly reference their antecedents

### Common Pitfalls to Avoid

❌ **DON'T** label every action as DIVINE_ACTION or HUMAN_ACTION—only when the subject is clear and the action is significant

❌ **DON'T** over-apply METAPHORICAL—use more specific labels when available (CHRISTOLOGY, TYPOLOGY, PARABLE_IMAGE)

❌ **DON'T** forget context—"rock" could be OBJECTS_NATURAL or METAPHORICAL depending on usage

❌ **DON'T** ignore pronouns—they carry theological significance (DIVINE_PRONOUN vs HUMAN_PRONOUN)

❌ **DON'T** conflate TITLE with PERSON—"King David" has both labels on different spans

✅ **DO** prioritize theological precision over frequency—better to skip uncertain cases

✅ **DO** use NULL for genuinely ambiguous or unclassifiable terms

✅ **DO** maintain consistency with the curated gazetteers

✅ **DO** defer to Strong's concordance for lexical precision

---

## Quick Reference Index

### By Theological Domain

**Theology Proper** (God the Father)
- DEITY
- DIVINE_TITLE
- DIVINE_PRONOUN
- DIVINE_ACTION
- DIVINE_COMMAND
- DIVINE_PROMISE

**Christology** (God the Son)
- CHRISTOLOGY
- DIVINE_TITLE (when applied to Christ)
- TYPOLOGY (OT foreshadows)

**Pneumatology** (God the Holy Spirit)
- PNEUMATOLOGY
- DIVINE_PRONOUN (when Spirit speaks)

**Soteriology** (Salvation)
- SOTERIOLOGY
- COVENANT_TERM
- SIN
- LAW_COMMANDMENT

**Ecclesiology** (The Church)
- ECCLESIOLOGY
- HUMAN_COLLECTIVE (when referring to congregation)

**Eschatology** (End Times)
- ESCHATOLOGY
- PROPHECY_FORMULA
- TIME (eschatological markers)

**Angelology/Demonology** (Spiritual Beings)
- ANGEL_CHORUS
- SPIRITUAL_ENTITY
- DEMON
- SATANIC_TITLE

**Hamartiology** (Sin)
- SIN
- CURSE_FORMULA

**Worship & Practice**
- RITUAL_PRACTICE
- LITURGICAL_TERM
- BLESSING_FORMULA
- OATH_FORMULA

### By Literary Function

**Narrative Elements**
- PERSON
- LOCATION
- TIME
- HUMAN_ACTION

**Poetic/Figurative Language**
- METAPHORICAL
- METONYMY
- PARABLE_IMAGE

**Discourse Markers**
- HERMENEUTIC_KEY
- GENRE_MARKER
- INTERTEXTUAL_REF
- PROPHECY_FORMULA

**Descriptive**
- BIBLE_ANIMALS
- BIBLE_FLORA
- OBJECTS_MANMADE
- OBJECTS_NATURAL
- BODY_PART

### Alphabetical Label List

1. ANGEL_CHORUS
2. BIBLE_ANIMALS
3. BIBLE_FLORA
4. BIBLE_NATIONS
5. BLESSING_FORMULA
6. BODY_PART
7. CHRISTOLOGY
8. CONCEPT
9. COVENANT_TERM
10. CULTURAL_PRACTICE
11. CURSE_FORMULA
12. DEITY
13. DEMON
14. DIVINE_ACTION
15. DIVINE_COMMAND
16. DIVINE_PROMISE
17. DIVINE_PRONOUN
18. DIVINE_TITLE
19. ECCLESIOLOGY
20. ECONOMIC_TERM
21. ESCHATOLOGY
22. FALSE_GOD
23. FOOD
24. GENEALOGY_REF
25. GENERIC_PRONOUN
26. GENRE_MARKER
27. HERMENEUTIC_KEY
28. HUMAN_ACTION
29. HUMAN_COLLECTIVE
30. HUMAN_PRONOUN
31. INTERTEXTUAL_REF
32. LAW_COMMANDMENT
33. LITURGICAL_TERM
34. LOCATION
35. METAPHORICAL
36. METONYMY
37. NUMBER
38. NUMERIC_MEASURE
39. NUMERIC_SYMBOLISM
40. OATH_FORMULA
41. OBJECTS_MANMADE
42. OBJECTS_NATURAL
43. OTHER
44. PARABLE_IMAGE
45. PERSON
46. PNEUMATOLOGY
47. PROPHECY_FORMULA
48. PROPHET
49. RITUAL_PRACTICE
50. SATANIC_TITLE
51. SIN
52. SOTERIOLOGY
53. SPIRITUAL_ENTITY
54. THEMES
55. TIME
56. TITLE
57. TOOLS_MEASUREMENT
58. TOPICAL_NOUNS
59. TRANSLATION_NOTE
60. TYPOLOGY
61. VERB

---

## Implementation Notes

### Strong's Concordance Integration

The taxonomy heavily leverages Strong's Concordance numbers for precise lexical identification:

- **H-numbers**: Hebrew/Aramaic Old Testament (e.g., H3068 = YHWH)
- **G-numbers**: Greek New Testament (e.g., G2316 = theos/God)

Key Strong's entries include:
- **DEITY**: Core divine names (YHWH, Elohim, Theos)
- **RITUAL_PRACTICE**: Sacrificial system terminology (22+ Strong's IDs)
- **TYPOLOGY**: OT figures/objects pointing to Christ (14+ Strong's IDs)
- **TIME**: Day, time, Sabbath, Passover (6+ Strong's IDs)
- **TITLE**: Family relationships (son, daughter, father)
- **SPIRITUAL_ENTITY**: Cherub, watcher

### Gazetteer Files

Each label may reference one or more gazetteer files containing curated word lists:

```
./gazetteers/ANGEL_CHORUS.txt
./gazetteers/BIBLE_ANIMALS.txt
./gazetteers/BIBLE_FLORA.txt
./gazetteers/BIBLE_NATIONS.txt
[... 61 total gazetteer files ...]
```

These files represent:
- High-confidence terms extracted from your 15,834-word biblical database
- Curated lists from your JSON categorizations
- Approved vocabulary aligned with Calvary Chapel teaching

### Default Behavior

**When No Label Matches**: `label_on_miss: NULL`

This preserves spans that genuinely cannot be classified, maintaining annotation integrity.

---

## Version Control & Updates

**Current Version**: Based on label_rules.yml (61 enabled labels)

**Future Considerations**:
- Additional experimental labels noted in comments (ETHNIC, ORG)
- Expansion of gazetteers as curated database grows
- Refinement of priority rules based on annotation experience

**Theological Review**:
All updates should maintain alignment with:
- Literal-grammatical-historical interpretation
- Chuck Smith / Calvary Chapel distinctive teaching
- Strong's Concordance lexical precision
- Spirit-led illumination as foundational principle

---

## Appendix: Sample Annotated Verse

**Genesis 1:1 (KJV)**
> "In the beginning [TIME] God [DEITY] created [DIVINE_ACTION] the heaven [OBJECTS_NATURAL] and the earth [OBJECTS_NATURAL]."

**John 1:1 (KJV)**
> "In the beginning [TIME] was the Word [CHRISTOLOGY], and the Word [CHRISTOLOGY] was with God [DEITY], and the Word [CHRISTOLOGY] was God [DEITY]."

**Exodus 12:11 (KJV)**
> "And thus shall ye eat it [OTHER]; with your loins [BODY_PART] girded, your shoes [OBJECTS_MANMADE] on your feet [BODY_PART], and your staff [OBJECTS_MANMADE] in your hand [BODY_PART]; and ye shall eat it in haste: it is the LORD'S [DIVINE_PRONOUN] passover [RITUAL_PRACTICE]."

**Matthew 5:14 (KJV)**
> "Ye are the light [METAPHORICAL] of the world [CONCEPT]. A city [LOCATION] that is set on an hill [OBJECTS_NATURAL] cannot be hid."

---

## Contact & Support

For theological questions regarding label application, consult:
- Strong's Concordance entries
- Chuck Smith commentaries (SermonIndex.net)
- Calvary Chapel distinctives documentation
- Project curated JSON files and gazetteers

For technical implementation:
- Refer to label_rules.yml for exact Strong's IDs and gazetteer paths
- Test annotations against the 24,121 labeled examples in your training set
- Validate against GoodBook.db (31,009 KJV verses) and concordance.db

---

**Document Status**: Comprehensive Taxonomy Guide v1.0
**Based On**: label_rules.yml with 61 enabled labels
**Last Updated**: November 2025
**Framework**: Literal-Grammatical-Historical Interpretation
**Purpose**: Bible Companion Project / Theological Heritage AI

