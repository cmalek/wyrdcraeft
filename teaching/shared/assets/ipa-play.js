const COMMONS_REDIRECT = "https://commons.wikimedia.org/wiki/Special:Redirect/file/";

const IPA_AUDIO = {
  open_back_a: {
    file: "Open_back_unrounded_vowel.ogg",
    label: "[ɑ] open back unrounded vowel",
  },
  ae: {
    file: "Near-open_front_unrounded_vowel.ogg",
    label: "[æ] near-open front unrounded vowel",
  },
  close_mid_e: {
    file: "Close-mid_front_unrounded_vowel.ogg",
    label: "[e] close-mid front unrounded vowel",
  },
  front_rounded_y: {
    file: "Close_front_rounded_vowel.ogg",
    label: "[y] close front rounded vowel",
  },
  close_back_u: {
    file: "Close_back_rounded_vowel.ogg",
    label: "[u] close back rounded vowel",
  },
  theta: {
    file: "Voiceless_dental_fricative.ogg",
    label: "[θ] voiceless dental fricative",
  },
  eth: {
    file: "Voiced_dental_fricative.ogg",
    label: "[ð] voiced dental fricative",
  },
  x: {
    file: "Voiceless_velar_fricative.ogg",
    label: "[x] voiceless velar fricative",
  },
  ccedilla: {
    file: "Voiceless_palatal_fricative.ogg",
    label: "[ç] voiceless palatal fricative",
  },
  esh: {
    file: "Voiceless_postalveolar_fricative.ogg",
    label: "[ʃ] voiceless postalveolar fricative",
  },
  gamma: {
    file: "Voiced_velar_fricative.ogg",
    label: "[ɣ] voiced velar fricative",
  },
  g_stop: {
    file: "Voiced_velar_plosive.ogg",
    label: "[g] voiced velar plosive",
  },
  d_ezh: {
    file: "Voiced_palato-alveolar_affricate.ogg",
    label: "[dʒ] voiced postalveolar affricate",
  },
  j: {
    file: "Palatal_approximant.ogg",
    label: "[j] palatal approximant",
  },
  k: {
    file: "Voiceless_velar_plosive.ogg",
    label: "[k] voiceless velar plosive",
  },
  t_esh: {
    file: "Voiceless_palato-alveolar_affricate.ogg",
    label: "[tʃ] voiceless postalveolar affricate",
  },
  tap_r: {
    file: "Alveolar_tap.ogg",
    label: "[ɾ] alveolar tap",
  },
  eng: {
    file: "Velar_nasal.ogg",
    label: "[ŋ] velar nasal",
  },
  h: {
    file: "Voiceless_glottal_fricative.ogg",
    label: "[h] voiceless glottal fricative",
  },
  i: {
    file: "Close_front_unrounded_vowel.ogg",
    label: "[i] close front unrounded vowel",
  },
};

let currentAudio = null;

document.querySelectorAll("[data-ipa-play]").forEach((node) => {
  const key = node.dataset.ipaPlay;
  const entry = IPA_AUDIO[key];
  const explicitFile = node.dataset.ipaFile;
  const explicitLabel = node.dataset.ipaLabel;
  if (!entry) {
    if (!explicitFile) {
      return;
    }
  }

  const label = explicitLabel || entry?.label || node.textContent.trim();
  const url = `${COMMONS_REDIRECT}${explicitFile || entry.file}`;

  node.type = "button";
  node.classList.add("ipa-play");
  node.title = `Play ${label}`;
  node.setAttribute("aria-label", `Play ${label}`);

  node.addEventListener("click", () => {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
    }
    currentAudio = new Audio(url);
    currentAudio.play().catch(() => {});
  });
});
