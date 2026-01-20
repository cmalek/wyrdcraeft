Standard JSON Representation for Old English Texts
==================================================

Overview and Requirements
-------------------------

Old English texts vary widely in structure - from prose chronicles and homilies to poetic epics and dialogues. To effectively import these into translation software, we need a standard JSON schema that can flexibly capture all structural features of the source material. Based on the criteria, the JSON representation must account for:

- **Hierarchical divisions**: Books, chapters, sections, acts/scenes,
etc., as applicable.
- **Paragraphs and Sentences**: Prose texts should be broken into
paragraphs and individual sentences.
- **Poetry lines and stanzas**: Verse texts need line breaks preserved;
stanzas or numbered verse sections should be represented.
- **Numbering systems**: Chapter numbers, verse numbers, chronological entries (e.g. annal years in a chronicle ), and any other numbering (Roman numerals, etc.) should be captured as metadata, not intermingled with the text.
- **Dialogue structure**: Dialogues (like plays or Q&A texts) should mark speaker names for each spoken segment. For example, the *Solomon and Saturn* dialogue poem includes speakers “Saturnus” and “Salomon” in alternating lines . The JSON should represent these turns with a speaker field.
- **Whitespace and formatting**: Significant whitespace such as
paragraph breaks, stanza breaks, or indentations should be preserved
by the structure (e.g. paragraphs as distinct JSON elements, blank
lines indicating stanza breaks, etc.). There's usually no need to
record every newline character, but blank lines that separate sections
(like stanza breaks in poems) might be represented as empty paragraphs
or a special marker.
- **Source references**: Include source bibliographic info (title, author, source URL or print edition) at the document level, and original page or folio numbers at a fine-grained level. For instance, if a sentence or line begins on a new page of the source, the JSON element for that sentence/line can carry a source_page number. In the Beowulf edition by Wyatt, the text indicates manuscript folio changes (e.g. “Fol. 129a” in the text ); the JSON could record these as page/folio markers attached to the relevant line or as special elements.

By designing the JSON with these requirements, we can handle a wide range of Old English texts - whether a continuous prose homily with paragraphs, a poem with numbered lines, or a play-like dialogue with speakers. The goal is to preserve content and structure without mixing them (e.g., store numbering or speaker metadata separately from the text content).

Proposed JSON Schema Design
---------------------------

To cover all the above, we propose a hierarchical JSON structure using nested objects for different levels of the text. At a high level, the JSON will have two parts: metadata (bibliographic info) and content (the text structure). Below is an outline of the structure and how each feature is represented:

- **Metadata**: An object containing fields like title (of the work), author (if known, e.g. Ælfric), source (e.g. URL or bibliographic citation), language (“Old English”), and optionally translator or editor if applicable. This is global info about the text
- **Content**: The content is represented as a tree of nested sections:
- **Top-level sections**: If the work is divided into large parts (like books in a longer work or acts in a play), each can be a section object with a type or label. Otherwise, the top level might just be the whole text or an array of chapters. For example, a Chronicle or Bible book might not have “books” within (since the Chronicle itself is a book; the Bible does have multiple books though). Our design allows an arbitrary level of nesting: e.g. a book contains chapters, which contain sections, etc.
- **Sections/Chapters**: Each section has an optional number and/or title. The number can be an integer or string - e.g. for chapter “III” we could store “number”: “III”, or for a chronicle year we might store “number”: 1066. Titles might be present (e.g. chapter titles or section headings) or null if the section is just numbered. Example: in Beowulf (Wyatt) the poem is divided into sections I, II, III… with no titles, whereas in Ælfric's homilies each sermon has a title (Latin and English) along with a number .
- **Paragraphs vs. Verses**: A section can contain either prose paragraphs or verse lines:
- **Paragraphs**: Each paragraph is an array of sentence objects. We split into sentences so that alignment with translations is easier and so that verse numbers or sentence numbers can be attached. For instance, a paragraph in the JSON might look like. This example shows two sentences from the West Saxon Gospel of Mark, with verse numbers 1 and 2 stored separately . The number field in a sentence holds verse or sentence identifier if present (otherwise it can be omitted).

.. code:: json

   {
      "sentences": [
         {"text": "Her ys godspelles angyn Hælendes Cristes, godes suna.", "number": 1},
         {"text": "Swa awriten is on ðæs witegan bec Isaiam,", "number": 2},
         ...
      ]
   }

- **Verses/Lines**: For poetry, instead of paragraphs we use a list of line objects. Each line object will have the line text and optionally a line number. For example, in Beowulf we would capture each poetic line as one JSON object, e.g. ``{ "text": "Hwæt! wē Gār-Dena in gēar-dagum", "number": 1 }``.  We do not include the in-text numbering like “5” or “10” that some editions print every 5 lines - those are editorial and can be omitted or handled in post-processing. Instead, we would number lines sequentially or use the actual line numbers from the critical edition (1-3182 for Beowulf). If the edition already numbers every line explicitly, we take those numbers. In Wyatt's edition, every 5th line number is given (5, 10, 15, … in the margin ); we can infer the others.
- **Stanzas or Verse Sections**: If a poem has clearly divided sections or stanzas (for instance, Deor is a short poem with paragraph-like stanzas, each ending in a refrain), we could introduce an intermediate section level for each stanza. In JSON this might be a section with a list of lines as children. This is optional and depends on the text - many Old English poems are continuous, but some (like The Wanderer in some editions, or Psalm translations) might be grouped.
- **Dialogue**: For texts with dialogue (plays, dialogues, etc.), we represent each speech turn as a paragraph with an attached speaker field. Essentially, a paragraph in a play is a character's speech.  Within that, we can still split into sentences if needed. For example, one entry might be:

.. code:: json

   {
      "speaker": "Saturnus",
      "sentences": [
         {
            "text": "Saga mē, hwelċ wyrt is betst and sēlost?"
            "number": null
            "source_page": null
            "confidence": null
         }
      ]
   }

followed by the response:

.. code:: json

   {
      "speaker": "Salomon",
      "sentences": [
         {
            "text": "Iċ þē secge, liliġe hātte sēo wyrt, for þām þe hēo ġetācnað Crist."
            "number": null
            "source_page": null
            "confidence": null
         }
      ]
   }

This captures a Q&A pair from Solomon and Saturn . In a verse dialogue (like the Solomon and Saturn poem ), we can either treat each verse line as its own unit with a speaker, or group a character's continuous lines into one paragraph. The JSON is flexible enough for either approach. A safe method is to start a new paragraph whenever a new speaker begins talking. Each such paragraph object has a speaker name and then either a list of sentences (if prose dialogue) or a list of lines (if poetic dialogue). For instance, in the poem JSON we might have:

.. code:: json

   {
      "speaker": "Saturnus",
      "lines": [
          {
            "text": "Hwæt! Ic iglanda eallra hæbbe boca onbyrged..."
            "number": null
            "source_page": null
            "confidence": null
          }
      ]
  }

Then the next object for Salomon's reply, etc. This way, the dialogue structure is preserved.

- **Origin Page Numbers**: To track where each part of the text came from in the source, each JSON element at the sentence or line level can carry a source_page (or folio, etc.) field. When parsing a PDF, for example, we know the page on which a given paragraph or line was found - this can be recorded. If working from a TEI or annotated source that marks manuscript folios, we can insert a dummy “page break” element in the JSON or annotate the first sentence after a break with a source_page. For example, in Beowulf, line 1 begins on manuscript folio 129a , so the JSON line 1 might include “source_page”: “folio129a”. This information is crucial for traceability but can be omitted if not available.
- **Handling of numbering and labels**: Numbering is stored in the JSON separate from the actual text content. This ensures that, say, “A.D.  449” at the start of a Chronicle entry can be split into a number field (449) and perhaps a fixed label “A.D.” or handled as part of the section's metadata, while the rest of the sentence text (“Her Mauricius…”) remains pure. Similarly, biblical verses use the number field in the sentence object (as shown above for verses 1, 2, 3 from Mark ). Chapter and section numbers are stored in their parent section object. By doing so, the JSON is clean for the translator to work with (only actual OE text in the text fields) but still retains all organizational markers.

Example JSON excerpt: To illustrate, here's a tiny fragment of what the JSON might look like for a simplified example - an Anglo-Saxon Chronicle entry that contains a bit of prose and a verse:

.. code:: json

   {
      "metadata": {
         "title": "Anglo-Saxon Chronicle (Parker MS)",
         "source": "Wikisource",
         "author": "Anonymous",
         "year": "c. 890-1070",
         "language": "Old English",
         "editor": null,
         "license": null
      },
      "content": {
         "sections": [
            {
               "number": 937,
               "title": null,
               "paragraphs": [
                  {
                     "sentences": [
                        {
                           "text": "Her Aethelstan cyning, eorla dryhten, beag-gifa, and his broðor eac, Eadmund aetheling,",
                           "number": null,
                           "source_page": 120,
                           "confidence": null
                        },
                        {
                           "text": "slogon æt Brunanburh on ane dæge...",
                           "number": null,
                           "source_page": 120,
                           "confidence": null
                        }
                     ]
                  }
               ],
               "lines": [
                  {
                    "text": "Ymbe Brunanburh board-weall clufon",
                    "number": 1,
                    "source_page": null,
                    "confidence": null
                    },
                  {
                    "text": "heowan heaþolinde hamora lāfan;",
                    "number": 2,
                    "source_page": null,
                    "confidence": null
                  },
               ]
            }
         ]
      }
   }

In this mock-up, we treat year 937 as a section with number “937”. It first has a paragraph (a prose introduction describing the Battle of Brunanburh) and then a list of lines which are the poetic celebration of the battle (the famous poem included in the Chronicle ). In practice, we might represent the whole poem as one object (e.g. a sub-section) separate from the prose. But this shows how the JSON can flexibly include both prose and verse under the same section. The source_page indicates these sentences came from page 120 of the source edition, for example.

Notice how the verse lines have a number (line numbers 1 and 2 of the poem fragment) whereas the prose sentences do not have a number except we could include one if, say, the source numbered the sentences (not common, but Bible verses did as shown earlier). The year “937” is stored as the section's number - we could also include a field like “era”: “AD” if needed, but that might be overkill.
Pydantic Models for the Schema
------------------------------

To implement this in Python (>3.9<=3.13) and ensure our JSON structure is valid, we can define Pydantic v2 models. These models will help in reading/writing the JSON and validating that all required fields are present. See the :ref:`schema_models` for the Pydantic models corresponding to the design above.

A few notes on these models
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- We use :attr:`~oe_json_extractor.models.schema.Section.sections` to allow recursive nesting of sections.  For example, a Section of type "Book I" could have ``sections=[ …chapters…]``. Pydantic's forward reference handling is set up so that it knows sections contains Section items.

- A :class:`~oe_json_extractor.models.schema.Section` can have either paragraphs or lines or even both. We can mix prose and verse in one section. The model does not enforce an XOR, but logically when populating it we will choose the appropriate field. If a section has both, it's interpreted that the section has some prose paragraphs and some lines of verse (as we illustrated).

- The :class:`~oe_json_extractor.models.schema.Paragraph` model includes an optional speaker. If present, this paragraph represents dialogue spoken by that person. In a non-dialogue context, speaker stays None.
- :class:`~oe_json_extractor.models.schema.Sentence` and :class:`~oe_json_extractor.models.schema.Line` both carry an optional :attr:`~oe_json_extractor.models.schema.Sentence.source_page` and :attr:`~oe_json_extractor.models.schema.Line.source_page` for granular traceability.
- :class:`~oe_json_extractor.models.schema.OldEnglishText` is the top-level model combining metadata and the content tree.

These models allow us to ingest source data by populating them (e.g., parse a
document into these structures) and then easily emit JSON via Pydantic's
``.model_dump()`` (or ``.json()``) methods. This ensures the output adheres to
the schema and is properly typed.

Parsing and Conversion Workflow with unstructured and any-llm
-------------------------------------------------------------

Deterministic Parsing Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To efficiently convert raw Old English texts into this JSON format, we mainly
use the deterministic approach of this package, which works like so:

- We start with a text file or PDF file.
- If it is PDF, we extract the text from the PDF using the ``unstructured`` library or the ``pdfplumber`` library.
- Now that we have text, we use a variety of heuristics to parse the text into sections, paragraphs, sentences, and lines.
- We identify which parts are prose and which are verse.
- We then build the JSON structure from the parsed text by assigning the appropriate fields to the JSON structure.

AI Assisted Parsing Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. important::
  LLM based partitioning and extraction is implemented in this package, but it is experimental and does not work as well as the deterministic approach.

  Specfically, it has a very hard time with verse; Old English verse is very particular about how it is structured, and so far I can't get the ``unstructured`` + ``any-llm`` analyze and parse it correctly.

To convert raw Old English texts into this JSON format, we can also leverage two
powerful Python libraries: ``unstructured`` and ``any-llm``.

- ```unstructured`` <https://unstructured.io>`__: This library provides
  robust tools to ingest various document formats (PDF, DOCX, HTML,
  etc.) and break them into structured elements . We can feed an OE text
  file or PDF to partition functions of ``unstructured``, and it will
  return a list of elements like “Title”, “NarrativeText” (for
  paragraphs), “ListItem”, “PageBreak”, etc., each with associated
  metadata . Notably, ``unstructured`` preserves page numbers in the
  element metadata when parsing PDFs , which we can use to fill the
  source_page in our JSON. It also identifies headings versus body text,
  which helps in detecting section titles. Using ``unstructured`` as a
  first pass, we get a raw structured text: e.g., we might get back a
  sequence of paragraphs (with their text content) and headings (with
  text like “Chapter I”) that we can interpret. This significantly
  simplifies extracting paragraphs and basic hierarchy from sources that
  are PDF scans or HTML pages. In short, ``unstructured`` will handle
  the heavy lifting of text extraction from diverse formats while
  maintaining structure and metadata.
- ```any-llm`` <https://github.com/google/langextract>`_ Allows us to use any
  LLM to extract the structured data from the text, especially locally hosted
  LLMs like ``ollama``.  After we have the text partitioned by
  ``unstructured``, we might still need to interpret and fine-tune the
  structure - for example, identifying that “II” is a chapter number, or
  splitting a paragraph by sentences correctly if not already done.
  ``any-llm`` is ideal for this next step, because it allows us to use any LLM,
  not just the ones that are supported by ``langextract``. We define our
  user instructions and examples for extracting structured data from
  text with the help of an LLM (like Google's Gemini) . We can prompt
  ``any-llm`` to, say, “Extract a JSON with chapters, verses,
  speakers, etc. from this text,” providing a few-shot example of the
  desired JSON format. LLMs are quite good at enforcing the output schena,
  though they are not great at preserving structure like poetry stanzas.

AI Workflow summary
~~~~~~~~~~~~~~~~~~~

- We run ``unstructured`` to get elemental chunks of text with metadata.
- We preprocess the text to identify all the text which is most likely to be Old English.
- We then use ``any-llm`` to extract the structured data from the text chunks, using tailored prompts for prose and verse and model.
- We then validate the output against our Pydantic models.
- We then emit the JSON.

Survey of Old English Text Sources and Formats
----------------------------------------------

As part of this project, we surveyed numerous Anglo-Saxon text sources to
understand their formats and features. Below is a report of key sources,
including their URLs, approximate lengths, and the notable structural features
each contains:

- *Anglo-Saxon Chronicle* (Parker MS, Corpus Christi Cambridge) -
  Original Old English annals, available via
  `Wikisource <https://en.wikisource.org/wiki/Anglo-Saxon_Chronicle_(A)>`__.
  Length: ~30,000 words. Format: HTML transcription. Features: Yearly
  annal entries serving as sections (each entry starts with a year like
  “449” or “A.D. 449” as a heading/number). Mostly prose paragraphs, but
  interspersed with poetry in certain years (e.g. the Battle of
  Brunanburh poem in 937 is presented as verse lines) . Contains many
  numeric expressions (dates, regnal years, genealogy) often written in
  Roman or Old English numerals (e.g. “.xvii. gear” for “17 years” in
  the text ). No overall chapters - entries are chronological. We will
  treat each year as a section with the year as its number. Original
  manuscript page/folio markers are not in this transcription (it's a
  continuous text), but we can use the year as a unique ID per entry.
  Dialogue: none (though direct speech may appear within narrative, it's
  not formatted as dialogue).
- *Beowulf* (Wyatt's edition, 1894) Old English epic poem, with text
  available on
  `Wikisource <https://en.wikisource.org/wiki/Beowulf_(Wyatt)>`__ .
  Length: ~3,182 lines (around 25k words). Format: HTML transcription of
  a printed edition. Features: Fully poetic text divided into numbered
  sections or “fitts” I-XLIII (these are editorial; the manuscript
  itself isn't divided, but Wyatt added divisions with Roman numerals
  and line ranges ). We have line numbers marked every 5 lines in the
  edition (e.g. marginal 5, 10, 15… ), which we'll expand to every line
  in JSON. The text includes extensive footnotes and critical apparatus:
  footnote callouts [1], [2] appear in-line , with footnote text
  explaining manuscript readings (e.g. missing letters, conjectures).
  For our purposes, the footnotes can be omitted from the main JSON
  content (or collected in a separate field) since we only need the OE
  text itself. Source info: The edition provides manuscript folio
  references (e.g. “Fol. 129a” at the start ) and page numbers of the
  book. We can capture those as source_page (e.g. Folio 129a for line
  1). No dialogues in Beowulf (it’s third-person narration with embedded
  speeches, but those are not formatted as separate speaker turns).
- *Solomon and Saturn* (Pater Noster Dialogue) Old English verse
  dialogue, available via the `Sacred-Texts
  archive <https://sacred-texts.com/neu/ascp/a13.htm>`__ . Length: ~150
  lines (~1,000 words). Format: HTML page. Features: Alliterative poetry
  written as a conversation between two characters. The text is
  structured as alternating speeches: lines or blocks prefixed by
  speaker names “Saturnus cwæð:” or “Salomon cwæð:”. This is essentially
  a dramatic dialogue in verse. Our JSON will capture each speaker’s
  lines with a speaker attribute. The edition numbers every 5th line (5,
  10, 15…) in the left margin, which we will convert to actual line
  indices in sequence. There are also some gaps or illegible words in
  this text (represented by ellipses or blanks like “M… …ces” in line 20
  ), but that does not affect the structure (we may just keep the
  ellipsis in the text string). Source: This is a modern transcription;
  no explicit page breaks given (the HTML is one continuous page). We
  might manually set source_page to sections if we know from a print
  source, but likely unnecessary.
- *West-Saxon Gospels* Gospel of Mark (Bright's 1904 edition of the West
  Saxon translation of the Bible) - Old English Bible text, Mark's
  Gospel available on
  `Wikisource <https://en.wikisource.org/wiki/The_Gospel_of_Saint_Mark_in_West-Saxon>`__.
  Length: ~7,000 words (16 chapters). Format: HTML transcription
  (scan-backed). Features: Chapters and verses: The text is clearly
  divided into chapters (I-XVI) with each chapter labeled (the edition
  uses the heading “Heafodweard” for each chapter, an OE word for
  “chapter”? ). Within chapters, every verse is numbered in-line. For
  example, chapter 1 starts with “1 Her ys godspelles angyn…” and the
  next sentence begins “2 Swa awriten is…” . We will use a section for
  each chapter (with number=1…“16”) and within it break the text by
  verses. Likely we will treat each verse as a Sentence in JSON,
  including its number. There are also section headings within chapters
  in this edition (e.g. at Mark 1:9 a heading “Þæt fullwiht Iesus”
  appears mid-chapter ). These are editorial headings for pericopes. We
  can represent such headings as either a special kind of paragraph with
  maybe title field, or as a subsection with no number but a title. For
  simplicity, we might include those as a standalone Paragraph with no
  sentences (or a dummy sentence) but with title=“Þæt fullwiht Iesus” to
  indicate a sub-heading. Dialogue: Dialogue in the gospels (Jesus
  speaking, etc.) is quoted within the narrative and marked with
  quotation marks in modern editions, but not as a dramatic format. So
  we do not treat it as dialogue turns - it will remain part of the
  paragraph text.
- *Ælfric's Lives of Saints* (EETS, Skeat 1881) Old English prose
  sermons, a large collection. Length: Very large (two volumes, each
  ~40k words of OE). Format: Scanned edition with parallel translation
  (OE and Modern English on facing pages). On Wikisource, it's partially
  available; the content is structured by individual “Life” (chapter) .
  Features: Chapters/ sermons: Each Life of a Saint is like a chapter,
  often with a Latin title and an English title (e.g. “De Sco̅ Marco
  euangelista - XV - Of Saint Mark the Evangelist (Apr. 25)” ). We will
  create sections for each life, using the Roman numeral or the title as
  the identifier. Paragraphs: The homilies are prose, divided into
  paragraphs. Some may have numbered lists or biblical verse references
  internally. No verse-line structure since it's not poetry. Dialogue:
  Generally narrative or expository; no formatted dialogue, though
  direct speech may occur (quotations from saints, etc.). Notes: Because
  the edition prints OE and modern English side by side, using
  ``unstructured`` on the PDF will likely yield alternating paragraphs
  of OE and translation. We must filter/extract only the OE text.
  Possibly we'll identify the language of each chunk (maybe by detecting
  characters with macrons or known OE words) - this is where an AI
  extraction approach could help (tell ``any-llm`` to separate Old
  English text from the modern translation). Source metadata: We have
  page numbers from the printed edition which we can use as source_page.
  E.g., each homily starts on a new page with a heading. Capturing those
  could be useful if we want to sync with the print source.
- “The Wanderer” and other shorter Exeter Book poems - Old English
  poetry, often in plain text format (various online sources such as
  Tony Jebson's “Exeter Book” collection). Length: a few hundred words
  each. Format: Usually plain text or HTML without line numbers.
  Features: These are purely poetic (no sections or chapters), sometimes
  with irregular line breaks or indentation (e.g. *The Wanderer* has a
  short introductory rubric and then verses; *Deor* has refrain lines).
  We will treat each as a single section containing a list of line
  objects. If there's a refrain or repeated line (like *Deor*'s “Þæs
  ofereode, þisses swa mæg”), we just include it as a normal line in
  sequence. No special numbering beyond line numbers (which we can
  assign sequentially if not given). No dialogue or substructure. These
  texts help confirm that our schema covers simple cases gracefully (a
  section with just lines).

Each of the above sources was analyzed to ensure our JSON model can accommodate
it. We found that a flexible nested structure with optional fields (as
presented) is capable of representing all these cases. The use of tools like
unstructured and ``any-llm`` will streamline converting each source:

- E.g., for the *Chronicle*, ``unstructured`` can separate each year entry
(perhaps as paragraphs starting with a year), and we'll add logic to mark the
year as a section number.
- For *Beowulf*, ``unstructured`` theoretically could get us the lines (likely
each line as a separate “NarrativeText” element since each line ends with hard
line break in the PDF), and we can then easily number them and drop footnote
texts.
- For parallel-text homilies, ``unstructured`` will get both languages; we might
use ``any-llm`` or even a simpler script to split OE vs modern, then proceed
with OE paragraphs.

In conclusion, the standard JSON representation defined here, backed by Pydantic
models, can uniformly capture the diverse structural features of Old English
texts. It provides a clear separation of content, metadata, and structure, which
will greatly facilitate loading texts into the translation software and aligning
them with translations or other annotations. By leveraging the strengths of
contemporary parsing libraries, we can automate much of the conversion, ensuring
the resulting JSON is comprehensive and faithful to the source material's
format.
