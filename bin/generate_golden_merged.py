#!/usr/bin/env python3
"""Generate tests/fixtures/dictionary/golden_merged.jsonl from BT source data.

Run from the repository root:
    python bin/generate_golden_merged.py

This script parses selected BT lines through the full Phase-01..04 pipeline
and serialises the resulting BTConsolidatedEntry objects to JSONL.
"""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from wyrdcraeft.models.dictionary import BTSense  # noqa: E402
from wyrdcraeft.services.dictionary.editorial_merger import BTEditorialMerger  # noqa: E402
from wyrdcraeft.services.dictionary.line_parser import BTLineParser  # noqa: E402
from wyrdcraeft.services.dictionary.sense_segmenter import BTSenseSegmenter  # noqa: E402

# ---------------------------------------------------------------------------
# Selected BT raw line texts (from data/oe_bt.txt), keyed by group ID.
# Each entry is a list of (line_no, raw_line) pairs.
# ---------------------------------------------------------------------------

_SELECTED_GROUPS: dict[str, list[tuple[int, str]]] = {
    # ----------------------------------------------------------------
    # abbad — MAIN only (no add line in BT source for abbad itself)
    # ----------------------------------------------------------------
    "abbad-main": [
        (
            37,
            "abbad@<B>abbad,</B> abbod, abbud, abbot, es; <I>m:</I> abboda, an; <I>m.</I>"
            " I. <I>an abbot;</I> abbās, -- the title of the male superior of certain"
            " religious establishments. In point of dignity an abbot is generally next"
            " to a bishop :-- Se ārwurða abbad Albīnus <I>the reverend abbot Albinus,</I>"
            " Bd. pref. II. <I>bishops were sometimes subject to an abbot, as they were"
            " to the abbots of Iona</I> :-- Nū, sceal beōn ǣfre on Iī abbod,"
            " and nā biscop <I>now, in Iī, there must ever be an abbot, not a bishop,</I>"
            " Chr. 565; Th. 32, 10-16, col. l."
            " [<I>Laym.</I> abbed: <I>O. Frs.</I> abbete.]"
            " DER. abbad-dōm, -hād, -isse, -rīce: abboda.@abbad",
        ),
    ],
    # ----------------------------------------------------------------
    # abbod-hād — MAIN (line 53/abbud-had) + ADD (line 45/abbod-had)
    # Both parse under different norm_keys, so we use abbud-had MAIN + add
    # from the abbodhad variant as separate groups.
    # ----------------------------------------------------------------
    "abbudhad-main-only": [
        (
            53,
            "abbudhad@<B>abbud-hād,</B> es; <I>m. The state or dignity of an abbot;</I>"
            " abbatis dignitas :-- Munuchād and abbudhād ne syndon getealde to ðysum"
            " getele <I>monkhood and abbothood are not reckoned in this number,</I>"
            " L. Ælf. C. 18; Th. ii. 348, 31.@abbud-had",
        ),
    ],
    "abbodhad-add-only": [
        (
            45,
            "abbodhad@<B>abbod-hād.</B> <I>Add:</I>-- Ðā ðe ðæne abbod tō abbodhāde"
            " gecuron <I>qui abbatem ordinant,</I> R. Ben. 124, 16. Sē ðe tō abbodhāde"
            " sceal <I>qui ordinandus est,</I> 118, 3.@abbod-had",
        ),
    ],
    # ----------------------------------------------------------------
    # ā-bǣdan — SUBSTITUTE line replacing main senses (substitute-as-seed)
    # ----------------------------------------------------------------
    "abaEdan-substitute": [
        (
            27,
            "abaedan@<B>ā-bǣdan.</B> <I>Substitute the following:</I>"
            " <B>I.</B> <I>to force, wring</I> :-- Ele ābǣdan and āwringan of þām bergum"
            " <I>ab olivis exigere oleum torquendo,</I> Gr. D. 250, 22."
            " <B>II.</B> <I>to compel</I>:-- Gif ðæt nȳd ābǣdeþ"
            " <I>cum exhiberi mysterium ipsa necessitas compellit,</I> Bd. l, 27; S. 497, 1."
            " <B>III.</B> <I>to demand, require.</I> (l) where the object is something"
            " needed :-- Nāniges fultumes ābǣdeþ siō lār"
            " <I>nullum adjutorium expostulet ratio,</I> Nar. 2, 2.@a-bædan",
        ),
    ],
    # ----------------------------------------------------------------
    # a-bitweōnum — MAIN (synthetic) + bare DELE → empty-senses entry
    # ----------------------------------------------------------------
    "abitweonum-main-then-dele": [
        (
            116,
            "abitweonum@<B>a-bitweōnum;</B> <I>prep. Between;</I> inter :--"
            " Sēt him a-bitweōnum <I>he sat between them.</I>@a-bi-tweonum,a-bitweonum",
        ),
        (
            117,
            "abitweonum@<B>a-bitweōnum</B>. <I>Dele</I>.@a-bi-tweonum,a-bitweonum",
        ),
    ],
    # ----------------------------------------------------------------
    # ā-dōn — MAIN + DELE_AND_ADD + ADD
    # ----------------------------------------------------------------
    "adon-main": [
        (
            497,
            "adon@<B>a-dōn;</B> <I>p.</I> -dyde; <I>impert.</I> -dō;"
            " <I>v. a. To take away, remove, banish;</I> tollere, ejicere :--"
            " Ne māgon ðē nū heonan adōn hyrste ða reādan"
            " <I>the red ornaments may not now take thee hence,</I> Exon. 99a; Th. 370, 14; Seel. 57."
            " Adō ða buteran <I>remove the butter,</I> L. M. 1, 36; Lchdm. ii. 86, 22."
            " Adō of ða buteran <I>take off the butter,</I> 86, 19.@a-don",
        ),
        (
            498,
            "adon@<B>ā-dōn.</B> <I>Dele</I> Ælfc. T. 5, 25: Gen. 7, 23: 9, 11,"
            " <I>and add: with words further marking removal,</I>"
            " (1) fram:--Ic ādyde (<I>abstuli</I>) hosp fram eōwrum cynne, Jos. 5, 9."
            " Ādoo from ðē ðā byrðenne, Past. 225, 11."
            " (2) of:--Hē ādēð eōw of ðisse worulde, Bt. 19; F. 70, 17.@a-don",
        ),
        (
            499,
            "adon@<B>ā-dōn.</B> <I>Add:</I> -- Hungor ādyde hī. Chr. 1086."
            " Ādōþ gatu <I>tollite portas,</I> Ps. Rdr. 23, <I>J.</I>@a-don",
        ),
    ],
    # ----------------------------------------------------------------
    # ā-bisgung — SUBSTITUTE-as-seed (no old MAIN; supplements ā-bysgung)
    # ----------------------------------------------------------------
    "abisgung-substitute-for-x": [
        (
            110,
            "abisgung@<B>ā-bisgung</B> e; <I>f. Substitute the following for</I>"
            " ā-bysgung <I>in Dict</I>."
            " <B>I</B>. <I>occupation, employment, business</I>. v. ā-bisgian, I :--"
            " For ðǣre ūterran ābisgunge . . . for ðǣre ābisgunge ðāra ūterra weorca"
            " <I>in exteriorum occupatione</I>. Past. 127, 9, 12."
            " <B>II</B>. <I>trouble, disturbance</I>. v. ā-bisgian, II :--"
            " Hit is cūð ðætte siō ūterre ābisgung ðissa worold-ðinga ðæs monnes mōd"
            " gedrēfð and hine scofett hidres ðædres"
            " <I>constet, quod cor externis occupationum tumultibus impulsum a semetipso corruat</I>."
            " Past. 169, 12.@a-bisgung",
        ),
    ],
    # ----------------------------------------------------------------
    # a homograph: adv (ā) vs. noun/prep (a)
    # ----------------------------------------------------------------
    "a-adv": [
        (
            3,
            "a@<B>ā,</B> aa, aaa; <I>adv. Always, ever, for ever;</I>"
            " hence the <I>O. Eng.</I> AYE, <I>ever;</I> semper, unquam, usque :--"
            " Ac ā sceal ðæt wiðerwearde gemetgian"
            " <I>but ever must the contrary moderate.</I> Bt. 21; Fox 74, 19.@a,-a,a-",
        ),
    ],
    "a-prep": [
        (
            2,
            "a@<B>a;</B> <I>prep. acc. To, for;</I> in :--"
            " A worlda world <I>to or in an age of ages;</I>"
            " in seculorum seculum, Ps. Th. 18, 8.@a,-a,a-",
        ),
    ],
    # ----------------------------------------------------------------
    # Additional entries to reach ≥30 groups
    # ----------------------------------------------------------------
    "aac-single": [
        (
            6,
            "aac@<B>aac,</B> e; <I>f. An oak:</I> -- Aac-tūn <I>Acton Beauchamp,"
            " Worcestershire,</I> Cod. Dipl. 75 ; A. D. 727; Kmbl. i. 90, 19. v. Āc-tūn.@aac",
        ),
    ],
    "aad-single": [
        (
            5,
            "aad@<B>aad</B> <I>a pile</I> :-- He mycelne aad gesomnode"
            " <I>he gathered a great pile,</I> Bd. 3, 16; S. 542, 22. v. ād.@aad",
        ),
    ],
    "abacan-main": [
        (
            10,
            "abacan@<B>a-bacan,</B> ic -bace, ðū -bæcest, -bæcst, he -bæceþ, -bæcþ,"
            " <I>pl.</I> -bacaþ; <I>p.</I> -bōc, <I>pl.</I> -bōcon; <I>pp.</I> -bacen"
            " <I>To bake;</I> pinsere, coquere :-- Se hlāf þurh fȳres hǣtan abacen"
            " <I>the bread baked by the heat of fire.</I> Homl. Pasc. Daye, A. D, 1567,"
            " p. 30, 8.@a-bacan",
        ),
    ],
    "abacan-add": [
        (
            11,
            "abacan@<B>a-bacan</B> <I>to bake:</I>-- Nim ælces cynnes melo and ābacæ man"
            " hlāf, Lch. i. 404, 5. Þost tō cicle ābacen, 364, 15: Gr. D. 87, 21.@a-bacan",
        ),
    ],
    "abbadisse-main": [
        (
            40,
            "abbadisse@<B>abbadisse,</B> abbodisse, abbatisse, abbudisse, abedisse, an;"
            " <I>f.</I> [abbad <I>an abbot,</I> isse <I>a female</I> termination, <I>q. v.</I>]"
            " <I>An abbess;</I> abbatissa :-- Riht is ðæt abbadissan fæste on mynstrum"
            " wunian <I>it is right that abbesses dwell closely in their nunneries,</I>"
            " L. I. P. 13; Th. ii. 320, 30.@abbadisse",
        ),
    ],
    "abbodrice-main": [
        (
            48,
            "abbodrice@<B>abbod-rīce,</B> abbot-rīce, es; <I>n. The rule of an abbot,"
            " an abbacy;</I> abbatia :-- On his tīme wæx ðæt abbodrīce swīðe rīce"
            " <I>in his time the abbacy waxed very rich,</I> Chr. 656; Ing. 41, l.@abbod-rice",
        ),
    ],
    "abelgan-main": [
        (
            73,
            "abelgan@<B>a-belgan,</B> ic -beige, ðū -bilgst, -bilhst, he -bylgþ, -bilhþ,"
            " <I>pl.</I> -belgaþ; <I>p.</I> -bealg, -bealh, <I>pl.</I> -bulgon; <I>pp.</I>"
            " -bolgen, <I>v. trans.</I> [a, belgan <I>to irritate</I>]"
            " <I>To cause any one to swell with anger, to anger, irritate, vex, incense;</I>"
            " ira aliquem tumefacere, irritare, exasperare, incendere :--"
            " Ne sceal ic ðē abelgan <I>I would not anger thee,</I> Salm. Kmbl. 657; Sal. 328.@a-belgan",
        ),
    ],
    "aberan-main": [
        (
            81,
            "aberan@<B>a-beran;</B> <I>p.</I> -bær; <I>pp.</I> -boren."
            " I. <I>to bear, carry, suffer;</I> portare, ferre :--"
            " Ðe man aberan ne mæg <I>which they are not able to bear,</I> Mt. Bos. 23, 4."
            " II. <I>to take or carry away;</I> tollere, auferre :--"
            " Abær hine of eowdum sceāpa <I>sustulit eam de gregibus ovium,</I>"
            " Ps. Spl. 77, 76. v. beran.@a-beran",
        ),
    ],
    "abeodan-add": [
        (
            88,
            "abeodan@<B>ā-beōddan.</B> <I>Add:</I> (1) <I>to announce, declare a message</I>"
            " :-- Hē word ābeād <I>he delivered the words of his message,</I> B. 390."
            " (2) <I>to announce</I> what is coming:-- Heāhengel hǣlo ābeād Marian."
            " (3) <I>to bid</I> farewell:-- Hē hǣlo ābeād heorðgeneātum"
            " <I>he bade farewell to his comrades</I>, B. 2418.@a-beodan",
        ),
    ],
    "abeatan-add-no-senses": [
        (
            86,
            "abeatan@<B>ā-beatan.</B> <I>Add:</I>-- Ic ðē ðīne tēþ of ābeāte,"
            " Lch. i. 326, 15.@a-beatan",
        ),
    ],
    "ablisian-single": [
        (
            140,
            "ablisian@<B>a-blīsian;</B> <I>p.</I> ode; <I>pp.</I> od"
            " <I>To blush;</I> erubescere :-- Oðð eōwre lyðere mōdd ablīsige"
            " <I>donec erubescat incircumcisa mens eorum.</I> Lev. 26, 41.@a-blisian",
        ),
    ],
    "abarian-main-add": [
        (
            20,
            "abarian@<B>a-barian;</B> <I>. p.</I> ede; <I>pp.</I> ed"
            " [a, barian <I>to make bare;</I> bær, se bara; <I>adj.</I> <I>bare</I>]"
            " <I>To make bare, to manifest, discover, disclose;</I>"
            " denudare, prodere, in medium proferre :--"
            " Gif ðū abarast ūre sprǣce <I>si sermonem nostrum profers in medium,</I>"
            " Jos. 2, 20.@a-barian",
        ),
        (
            21,
            "abarian@<B>ā-barian.</B> <I>Add:</I> <B>I.</B> <I>to make bare, strip</I>"
            " :-- Stōwe rōde ābarude <I>locum cruce denudatum,</I> Angl. xiii. 427, 894."
            " <B>II.</B> <I>to lay bare, expose, disclose:</I>-- Ælfremeda wunda nā ābarian"
            " (<I>detegere</I>) and geswutelian, R. Ben. I. 80, 12.@a-barian",
        ),
    ],
    "abedan-simple": [
        (
            79,
            "abedan@<B>a-beden</B> <I>asked,</I> Nicod. 12; Thw. 6, 15: Bd. 4, 10;"
            " S. 578, 31; <I>pp. of</I> a-biddan.@a-beden",
        ),
    ],
    "abeofian-single": [
        (
            90,
            "abeofian@<B>a-beofian</B>"
            " <I>To be moved or shaken, to tremble;</I> moveri, contremere :--"
            " Ealle abeofedan eorðian staðalas"
            " <I>movebuntur omnia fundamenta terrae,</I> Ps. Th. 81, 5. v. beofian.@a-beofian",
        ),
    ],
    "abeornan-add": [
        (
            91,
            "abeornan@<B>ā-beornan</B> (-bi(e)rnan). <I>Add:</I> :--"
            " Ābyrnðð <I>exardescit</I>, Ps. L. 38, 4."
            " Hē ābarn (<I>exarsit</I>) mid ðē bryne wælhreōwnesse, Gr. D. 162, 22.@a-beornan",
        ),
    ],
    "abecede-single": [
        (
            92,
            "abecede@<B>ābēcēdē;</B> <I>f. An ABC, alphabet:</I>--"
            " Seō forme ābēcēdē on ðām gerīme ys bītan pricon.@a-becede",
        ),
    ],
    "abaligan-single": [
        (
            15,
            "abaligan@<B>a-bæligan;</B> <I>p.</I> ode; <I>pp.</I> od"
            " <I>To offend, to make angry;</I> irritare, offendere :--"
            " Sceal gehycgan hæleða ǣghwylc þæt he ne abælige bearn waldendes"
            " <I>every man must be mindful that he offend not the son of the powerful,</I>"
            " Cd. 217; Th. 276, 27; Sat. 195. v. a-belgan, a-bylgan.@a-bæligan",
        ),
    ],
    "abeatan-main": [
        (
            85,
            "abeatan@<B>a-beātan;</B> <I>p.</I> -beōt; <I>pp.</I> -beāten"
            " <I>To beat, strike;</I> tundere, percellere :--"
            " Stormum abeātne <I>beaten by storms,</I> Exon. 21b; Th. 58, 26; Cri. 941."
            " v. beātan.@a-beatan",
        ),
    ],
    "abegendlic-adj": [
        (
            83,
            "abegendlic@<B>a-bēgendlīc;</B> <I>adj. Bending;</I> flexibilis,"
            " Som. v. a-bēgan.@a-begendlic",
        ),
    ],
    "abisgian-main": [
        (
            109,
            "abisgian@<B>ā-bisgian,</B> -bysgian; <I>p.</I> ode; <I>pp.</I> od;"
            " <I>v. a.</I> <I>To occupy, employ, keep busy;</I>"
            " occupare :-- Hī wurdon ābysgode mid ðǣm woroldlīcum þingum"
            " <I>they were kept busy with worldly things,</I>"
            " Past. 127, 9. Ābysgad <I>occupatus,</I> Wrt. Voc. ii. 51, 25.@a-bisgian",
        ),
    ],
    "amansumian-dele-and-add": [
        (
            2803,
            "amansumian@<B>ā-mānsumian.</B> <I>Dele bracket and add:</I>"
            " <B>I.</B> <I>to accurse:--</I>Heō nolde āgan þæs wælhreōwan hærereāf"
            " ac āmānsumode, Hml. A. 115, 426. Sī þeōs buruh āmānsumod"
            " <I>sit civitas haec anathema,</I> Jos. 6, 17."
            " <B>II.</B> as an ecclesiastical term, <I>to excommunicate:--</I>"
            " Gif gē ne dōð, ic eōw āmānsumige, Hml. Th. ii. 176, 13."
            " [<I>O. H. Ger.</I> ar-meinsamōn <I>excommunicare.</I>]@a-man-sumian,a-mansumian",
        ),
    ],
    "aslacian-main-add": [
        (
            4092,
            "aslacian@<B>ā-slacian;</B> <I>p.</I> ode <I>To slacken;</I>"
            " remittere :-- Nānum ne geyfelode ne āslacude, Bd. 4, 18; Sch. 437, 1.@a-slacian",
        ),
        (
            4093,
            "aslacian@<B>ā-slacian.</B> <I>Add:</I>"
            " <B>I.</B> <I>to slacken, become slack</I>, (l) physical :--"
            " Bid dæs mannes wæstm gebīged, his swura āslacod. Hml. Th. i. 614, 13."
            " <B>II.</B> <I>to make slack</I> :-- Āslacudæ, āsclacade <I>hebitavit</I>,"
            " Txts. 66, 491.@a-slacian",
        ),
    ],
    "awundrian-substitute": [
        (
            4930,
            "awundrian@<B>ā-wundrian.</B> <I>Substitute:</I>"
            " <B>I.</B> <I>to wonder, be astonished:--</I>"
            " Ic āwundrode <I>mirabar,</I> Gr. D. 244, 13."
            " <B>II.</B> <I>to wonder at, admire, magnify:--</I>"
            " Āuundradon God <I>magnificabant Deum,</I> Lk. L. 5, 26.@a-wundrian",
        ),
    ],
    "ceapian-dele-and-add": [
        (
            9947,
            "ceapian@<B>ceāpian.</B> <I>Dele last passage, and add:</I>"
            " <B>I.</B> <I>to trade, traffic</I> :-- Ceāpigas (ceōpigas, R.)"
            " <I>negotiamini,</I> Lk. L. 19, 13."
            " <B>II.</B> <I>to buy, purchase</I> (with gen.) :--"
            " Man wið þone here friðes ceāpode, Chr. 1004; P. 135, 24.@ceapian",
        ),
    ],
    "bletsian-main-add": [
        (
            7912,
            "bletsian@<B>bletsian,</B> bletsigan; <I>part.</I> bletsiende, bletsigende;"
            " <I>p.</I> ode, ade; <I>pp.</I> od, ad; <I>v. a.</I>"
            " <I>To</I> BLESS, <I>wish happiness, consecrate;</I> benedicere, consecrare :--"
            " Ic Ismael ēstum wille bletsian <I>I will bless Ishmael with favours,</I>"
            " Cd. 107; Th. 142, 5; Gen. 2357.@bletsian",
        ),
        (
            7913,
            "bletsian@<B>bletsian</B> <I>(from</I> blēdsian, bloedsian). <I>Add:</I>"
            " <B>I.</B> <I>to hallow, consecrate</I> :-- Genom se Hǣlend hlāf and bletsade,"
            " Mt. R. 26, 26."
            " <B>II.</B> <I>to call holy, adore</I> :-- Mec giē bledtsiges, Jn. L. 13, 13."
            " <B>III.</B> <I>to invoke divine favour upon</I> :-- Þæt ic þē bletsige, Gen. 27, 4."
            " <B>IV.</B> <I>to speak gratefully of</I> a person :--"
            " Eal rihtgelȳfed folc sceal hine bletsian, Bl. H. 167, 14.@bletsian",
        ),
    ],
    "abeornan-main-add": [
        (
            75,
            "abeornan@<B>a-beornan;</B> <I>p.</I> -bearn, -barn, <I>pl.</I> -burnon;"
            " <I>pp.</I> -bornen, <I>v. intrans. To burn;</I> exardere :--"
            " Fyr abarn <I>exarsit ignis,</I> Ps. Th. 105, 16. v. beornan.@a-beornan",
        ),
        (
            76,
            "abeornan@<B>ā-beornan</B> (-bi(e)rnan). <I>Add:</I> :--"
            " Ābyrnð <I>exardescit</I>, Ps. L. 38, 4."
            " Hē ābarn (<I>exarsit</I>) mid ðȳ bryne wælhreōwnesse, Gr. D. 162, 22."
            " Ðæt his mōd āburne (<I>exardesceret</I>), 337, 33."
            " Āburnon <I>exarserunt</I>, Ps. L. 117, 12.@a-beornan",
        ),
    ],
    "drugung-single": [
        (
            13541,
            "drugung@<B>drugung,</B> e; <I>f. A dryness, a dry place;</I>"
            " siccĭtas, inăquōsus lŏcus :-- Hī costadon God in drugunge"
            " <I>temtāvērunt Deum in siccĭtāte,</I> Ps. Surt. 105, 14.@drugung",
        ),
    ],
    "gar-main-add": [
        (
            22594,
            "gar@<B>gār;</B> <I>m. A spear;</I> hasta :--"
            " Gār oft þurhwōd fǣges feorhhūs, By. 296.@gar",
        ),
        (
            22595,
            "gar@<B>gār.</B> <I>Add;</I> <B>I.</B>"
            " <I>a weapon with a pointed head.</I> (1) where the use is uncertain :--"
            " Gār oft þurhwōd fǣges feorhhūs, By. 296."
            " <B>II.</B> <I>the head</I> of a weapon :--"
            " Gār sceal on sceafte, ecg on sweorde, Gn. Ex. 203.@gar",
        ),
    ],
}


def _parse_and_segment(
    parser: BTLineParser,
    segmenter: BTSenseSegmenter,
    line_no: int,
    raw_line: str,
) -> object:
    """Parse and segment one raw BT line."""
    parsed = parser.parse(line_no, raw_line)
    if parsed.skip_reason is None and parsed.raw_line is not None:
        # Attach senses via dataclass replace
        import dataclasses
        senses = segmenter.segment_parsed_line(parsed.raw_line.raw_text).senses
        parsed = dataclasses.replace(parsed, senses=senses)
    return parsed


def _entry_to_dict(entry: object) -> dict:
    """Convert a BTConsolidatedEntry to a serialisable dict."""
    return {
        "norm_key": entry.norm_key,
        "headword_raw": entry.headword_raw,
        "headword_macronized": entry.headword_macronized,
        "pos": entry.pos,
        "genders": list(entry.genders),
        "variants": list(entry.variants),
        "senses": [
            {"sense_label": s.sense_label, "gloss_en": s.gloss_en}
            for s in entry.senses
        ],
        "etymology": entry.etymology,
        "see_also": list(entry.see_also),
        "source_line_nos": list(entry.source_line_nos),
    }


def main() -> None:
    parser = BTLineParser()
    segmenter = BTSenseSegmenter()
    merger = BTEditorialMerger()

    output_path = PROJECT_ROOT / "tests" / "fixtures" / "dictionary" / "golden_merged.jsonl"

    records = []
    for group_id, line_specs in _SELECTED_GROUPS.items():
        parsed_lines = []
        source_lines = []
        for line_no, raw in line_specs:
            pl = _parse_and_segment(parser, segmenter, line_no, raw)
            parsed_lines.append(pl)
            source_lines.append({"line_no": line_no, "text": raw})

        entries, _ = merger.merge(parsed_lines)
        for entry in entries:
            records.append({
                "id": group_id,
                "source_lines": source_lines,
                "expected": _entry_to_dict(entry),
            })

    with open(output_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Written {len(records)} records to {output_path}")


if __name__ == "__main__":
    main()
