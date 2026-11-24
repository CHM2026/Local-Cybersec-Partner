"""Gestion multilingue de CyberSec Dashboard (français / anglais / arabe).

Chaque entrée de :data:`STRINGS` est un triplet ``(fr, en, ar)``. Les clés sont
stables et utilisées partout dans l'interface, y compris pour le journal : les
actions déjà enregistrées sont donc traduites à l'affichage lors d'un changement
de langue.

L'instance globale :data:`I18N` est la source de vérité ; la fonction :func:`tr`
est le raccourci utilisé par l'application.

En plus de ce dictionnaire, :func:`install_qt_translator` applique les catalogues
Qt embarqués avec PySide6 afin que les textes propres à Qt (boutons « OK » /
« Annuler », boîtes de dialogue de fichiers, etc.) suivent aussi la langue.
"""

from PySide6.QtCore import QCoreApplication, QLibraryInfo, QTranslator

LANGUAGES = {"fr": "Français", "en": "English", "ar": "العربية"}
LANG_INDEX = {"fr": 0, "en": 1, "ar": 2}


# clé: (français, english, العربية)
STRINGS = {
    # ── Général ────────────────────────────────────────────────────────────
    "app.suffix": (" | Outil de sécurité", " | Security tool", " | أداة أمنية"),
    "common.error": ("Erreur", "Error", "خطأ"),
    "common.warning": ("Attention", "Warning", "تحذير"),
    "common.info": ("Info", "Info", "معلومة"),
    "common.confirmation": ("Confirmation", "Confirmation", "تأكيد"),
    "common.confirm": ("Confirmer", "Confirm", "تأكيد"),
    "common.confirm_clear": ("Confirmer", "Confirm", "تأكيد"),
    "common.copied": ("Copié !", "Copied!", "تم النسخ!"),
    "common.unknown": ("Inconnu", "Unknown", "غير معروف"),
    "common.na": ("N/A", "N/A", "غير متاح"),
    "common.clear": ("🗑️  Effacer", "🗑️  Clear", "🗑️  مسح"),
    "common.copy": ("📋  Copier", "📋  Copy", "📋  نسخ"),
    "common.stop": ("⏹  Arrêter", "⏹  Stop", "⏹  إيقاف"),
    "common.no": ("Non", "No", "لا"),
    "common.yes": ("Oui", "Yes", "نعم"),
    "common.copied_text": (
        "copié dans le presse-papiers.", "copied to clipboard.", "تم نسخها إلى الحافظة."),

    # ── Navigation ─────────────────────────────────────────────────────────
    "nav.dashboard": ("⬡  Tableau de Bord", "⬡  Dashboard", "⬡  لوحة التحكم"),
    "nav.passwords": ("🔑  Mots de Passe", "🔑  Passwords", "🔑  كلمات المرور"),
    "nav.strength": ("💪  Force du MDP", "💪  Password Strength", "💪  قوة كلمة المرور"),
    "nav.hashing": ("🔒  Hachage", "🔒  Hashing", "🔒  التجزئة"),
    "nav.files": ("📄  Intégrité Fichier", "📄  File Integrity", "📄  سلامة الملف"),
    "nav.scanner": ("🔍  Scanner Ports", "🔍  Port Scanner", "🔍  ماسك المنافذ"),
    "nav.base64": ("⚙️  Base64", "⚙️  Base64", "⚙️  Base64"),
    "nav.network": ("🌐  Réseau", "🌐  Network", "🌐  الشبكة"),
    "nav.logs": ("📋  Journal", "📋  Log", "📋  السجل"),
    "nav.quit": ("🚪  Quitter", "🚪  Quit", "🚪  خروج"),
    "nav.language": ("🌐  Langue :", "🌐  Language:", "🌐  اللغة:"),
    "nav.theme": ("🎨  Thème :", "🎨  Theme:", "🎨  السمة:"),
    "theme.dark": ("Sombre", "Dark", "داكن"),
    "theme.light": ("Clair 2026", "Light 2026", "فاتح 2026"),
    "nav.capture": ("📸  Capture d'écran", "📸  Screenshot", "📸  لقطة شاشة"),

    # ── Tableau de bord ────────────────────────────────────────────────────
    "page.dashboard.title": ("Tableau de Bord", "Dashboard", "لوحة التحكم"),
    "page.dashboard.subtitle": (
        "Vue d'ensemble des outils de cybersécurité disponibles",
        "Overview of the available cybersecurity tools",
        "نظرة عامة على أدوات الأمن السيبراني المتاحة"),
    "dashboard.welcome": (
        "Bienvenue dans CyberSec Dashboard 🛡️",
        "Welcome to CyberSec Dashboard 🛡️",
        "مرحباً بك في CyberSec Dashboard 🛡️"),
    "dashboard.description": (
        "Cet outil regroupe les fonctionnalités essentielles de cybersécurité.\n"
        "Naviguez via le menu de gauche pour accéder aux différents modules.\n"
        "Mots de passe et fichiers ne quittent jamais la machine. Seules les cibles "
        "que vous indiquez sont contactées (scan, ping, DNS) — aucune donnée "
        "n'est envoyée à un tiers.",
        "This tool brings together essential cybersecurity features.\n"
        "Use the left menu to access the different modules.\n"
        "Passwords and files never leave your machine. Only the targets you specify "
        "are contacted (scan, ping, DNS) — no data is sent to a third party.",
        "تجمع هذه الأداة أهم ميزات الأمن السيبراني.\n"
        "استخدم القائمة على اليسار للوصول إلى الوحدات المختلفة.\n"
        "لا تغادر كلمات المرور والملفات جهازك أبداً. يتم الاتصال فقط بالأهداف "
        "التي تحددها (فحص، بينغ، DNS) — لا تُرسل أي بيانات إلى طرف ثالث."),
    "dashboard.system": ("ℹ️  Informations Système", "ℹ️  System Information", "ℹ️  معلومات النظام"),
    "dashboard.os": ("Système d'exploitation", "Operating system", "نظام التشغيل"),
    "dashboard.architecture": ("Architecture", "Architecture", "البنية"),
    "dashboard.processor": ("Processeur", "Processor", "المعالج"),
    "dashboard.machine": ("Nom de la machine", "Machine name", "اسم الجهاز"),
    "dashboard.python": ("Version Python", "Python version", "إصدار بايثون"),
    "dashboard.modules": ("  Modules Suggérés par Priorité", "  Suggested Modules by Priority", "  الوحدات المقترحة حسب الأولوية"),
    "dashboard.module.scanner": ("Scanner Ports", "Port Scanner", "ماسك المنافذ"),
    "dashboard.module.scanner.desc": ("Analysez les ports\nouverts d'un hôte", "Scan the open\nports of a host", "افحص المنافذ\nالمفتوحة لمضيف"),
    "dashboard.module.passwords": ("Générateur MDP", "Password Generator", "مولد كلمات المرور"),
    "dashboard.module.passwords.desc": ("Créez des mots de\npasse forts & sécurisés", "Create strong &\nsecure passwords", "أنشئ كلمات مرور\nقوية وآمنة"),
    "dashboard.module.strength": ("Force MDP", "Password Strength", "قوة كلمة المرور"),
    "dashboard.module.strength.desc": ("Évaluez la robustesse\nde vos mots de passe", "Assess the strength\nof your passwords", "قيّم قوة\nكلمات المرور الخاصة بك"),
    "dashboard.module.files": ("Intégrité", "Integrity", "السلامة"),
    "dashboard.module.files.desc": ("Vérifiez vos fichiers\npar empreinte crypto", "Check your files\nwith a crypto hash", "تحقق من ملفاتك\nباستخدام بصمة تشفيرية"),
    "dashboard.module.hashing": ("Hachage", "Hashing", "التجزئة"),
    "dashboard.module.hashing.desc": ("MD5 / SHA-1 / SHA-256\n/ SHA-512", "MD5 / SHA-1 / SHA-256\n/ SHA-512", "MD5 / SHA-1 / SHA-256\n/ SHA-512"),
    "dashboard.module.base64": ("Base64", "Base64", "Base64"),
    "dashboard.module.base64.desc": ("Encodez / décodez\nen Base64", "Encode / decode\nBase64 data", "ترميز / فك ترميز\nBase64"),
    "priority.high": ("Haute", "High", "عالية"),
    "priority.medium": ("Moyenne", "Medium", "متوسطة"),
    "priority.low": ("Basse", "Low", "منخفضة"),
    "priority.badge": ("{num} · {level}", "{num} · {level}", "{num} · {level}"),

    # ── Générateur de mots de passe ───────────────────────────────────────
    "page.passwords.title": ("Générateur de Mots de Passe", "Password Generator", "مولد كلمات المرور"),
    "page.passwords.subtitle": (
        "Générez des mots de passe forts grâce au module secrets (CSPRNG)",
        "Generate strong passwords with the secrets module (CSPRNG)",
        "أنشئ كلمات مرور قوية باستخدام وحدة secrets (CSPRNG)"),
    "passwords.config": ("⚙️  Configuration", "⚙️  Configuration", "⚙️  الإعدادات"),
    "passwords.length": ("Longueur :", "Length:", "الطول:"),
    "passwords.upper": ("Majuscules (A-Z)", "Uppercase (A-Z)", "أحرف كبيرة (A-Z)"),
    "passwords.lower": ("Minuscules (a-z)", "Lowercase (a-z)", "أحرف صغيرة (a-z)"),
    "passwords.digits": ("Chiffres (0-9)", "Digits (0-9)", "أرقام (0-9)"),
    "passwords.symbols": ("Symboles (!@#$%...)", "Symbols (!@#$%...)", "رموز (!@#$%...)"),
    "passwords.noambig": ("Exclure ambigus (0,O,I,l)", "Exclude ambiguous (0,O,I,l)", "استبعاد المتشابهات (0,O,I,l)"),
    "passwords.quantity": ("Nombre à générer :", "Number to generate:", "عدد الكلمات المراد توليدها:"),
    "passwords.generate": ("⚡  Générer", "⚡  Generate", "⚡  توليد"),
    "passwords.generated": ("🔑  Mots de Passe Générés", "🔑  Generated Passwords", "🔑  كلمات المرور المولدة"),
    "passwords.select_charset": (
        "Sélectionnez au moins un type de caractère.",
        "Select at least one character type.",
        "اختر نوعاً واحداً على الأقل من الأحرف."),
    "log.password_generated": ("Génération MDP", "Password generation", "توليد كلمة مرور"),
    "log.password_generated.detail": (
        "{count} mot(s) de passe · longueur {length}",
        "{count} password(s) · length {length}",
        "{count} كلمة مرور · الطول {length}"),

    # ── Force du mot de passe ──────────────────────────────────────────────
    "page.strength.title": ("Vérificateur de Force", "Strength Checker", "فاحص القوة"),
    "page.strength.subtitle": (
        "Analysez en temps réel la robustesse de vos mots de passe",
        "Analyze the strength of your passwords in real time",
        "حلل قوة كلمات المرور الخاصة بك في الوقت الفعلي"),
    "strength.input": ("🔐  Mot de Passe à Analyser", "🔐  Password to Analyze", "🔐  كلمة المرور المراد تحليلها"),
    "strength.placeholder": ("Entrez un mot de passe pour l'analyser...", "Enter a password to analyze...", "أدخل كلمة مرور لتحليلها..."),
    "strength.placeholder_short": ("Entrez un mot de passe...", "Enter a password...", "أدخل كلمة مرور..."),
    "strength.details": ("📊  Analyse Détaillée", "📊  Detailed Analysis", "📊  تحليل مفصل"),
    "strength.criteria": ("✅  Critères de Sécurité", "✅  Security Criteria", "✅  معايير الأمان"),
    "strength.level": ("Niveau : {level}", "Level: {level}", "المستوى: {level}"),
    "strength.veryweak": ("Très Faible 🔴", "Very Weak 🔴", "ضعيف جداً 🔴"),
    "strength.weak": ("Faible 🟠", "Weak 🟠", "ضعيف 🟠"),
    "strength.medium": ("Moyen 🟡", "Medium 🟡", "متوسط 🟡"),
    "strength.strong": ("Fort 🟢", "Strong 🟢", "قوي 🟢"),
    "strength.verystrong": ("Très Fort ✅", "Very Strong ✅", "قوي جداً ✅"),
    "strength.length8": ("Longueur ≥ 8", "Length ≥ 8", "الطول ≥ 8"),
    "strength.length12": ("Longueur ≥ 12", "Length ≥ 12", "الطول ≥ 12"),
    "strength.length16": ("Longueur ≥ 16", "Length ≥ 16", "الطول ≥ 16"),
    "strength.upper": ("Contient des majuscules", "Contains uppercase", "يحتوي على أحرف كبيرة"),
    "strength.lower": ("Contient des minuscules", "Contains lowercase", "يحتوي على أحرف صغيرة"),
    "strength.digits": ("Contient des chiffres", "Contains digits", "يحتوي على أرقام"),
    "strength.symbols": ("Contient des symboles", "Contains symbols", "يحتوي على رموز"),
    "strength.norepeat": ("Pas de répétitions (xxx)", "No repetitions (xxx)", "لا تكرارات (xxx)"),
    "strength.stat.length": ("Longueur", "Length", "الطول"),
    "strength.stat.upper": ("Majuscules", "Uppercase", "أحرف كبيرة"),
    "strength.stat.lower": ("Minuscules", "Lowercase", "أحرف صغيرة"),
    "strength.stat.digits": ("Chiffres", "Digits", "أرقام"),
    "strength.stat.symbols": ("Symboles", "Symbols", "رموز"),
    "strength.stat.entropy": ("Entropie (bits)", "Entropy (bits)", "الإنتروبيا (بت)"),
    "log.strength": ("Analyse Force", "Strength analysis", "تحليل القوة"),
    "log.strength.detail": ("Score: {score}% · {level}", "Score: {score}% · {level}", "النتيجة: {score}% · {level}"),

    # ── Hachage ────────────────────────────────────────────────────────────
    "page.hashing.title": ("Calculateur de Hash", "Hash Calculator", "حاسمة التجزئة"),
    "page.hashing.subtitle": (
        "Calculez les empreintes cryptographiques de n'importe quel texte",
        "Compute cryptographic hashes of any text",
        "احسب البصمات التشفيرية لأي نص"),
    "hashing.input": ("📝  Texte à Hacher", "📝  Text to Hash", "📝  النص المراد تجزئته"),
    "hashing.compute": ("🔒  Calculer les Hash", "🔒  Compute Hashes", "🔒  حساب التجزئة"),
    "hashing.results": ("🔑  Résultats", "🔑  Results", "🔑  النتائج"),
    "hashing.warning": (
        "⚠️  MD5 et SHA-1 sont obsolètes pour la sécurité. Préférez SHA-256+",
        "⚠️  MD5 and SHA-1 are obsolete for security. Prefer SHA-256+",
        "⚠️  MD5 و SHA-1 قديمان أمنياً. يُفضل SHA-256+"),
    "hashing.enter_text": ("Entrez un texte à hacher.", "Enter text to hash.", "أدخل نصاً لتجزئته."),
    "log.hash": ("Calcul Hash", "Hash computation", "حساب التجزئة"),
    "log.hash.detail": ("Texte de {length} caractères haché", "Hashed text of {length} characters", "تم تجزئة نص من {length} حرف"),
    "msg.hash_copied": ("Hash {algo} copié dans le presse-papiers.", "Hash {algo} copied to clipboard.", "تم نسخ تجزئة {algo} إلى الحافظة."),

    # ── Intégrité des fichiers ─────────────────────────────────────────────
    "page.files.title": ("Vérification d'Intégrité", "Integrity Check", "التحقق من السلامة"),
    "page.files.subtitle": (
        "Calculez et comparez les empreintes cryptographiques de vos fichiers",
        "Compute and compare cryptographic hashes of your files",
        "احسب وقارن البصمات التشفيرية لملفاتك"),
    "files.select": ("📂  Sélection du Fichier", "📂  File Selection", "📂  اختبار الملف"),
    "files.browse": ("📂  Parcourir", "📂  Browse", "📂  تصفح"),
    "files.algorithm": ("Algorithme :", "Algorithm:", "الخوارزمية:"),
    "files.calculate": ("⚡  Calculer", "⚡  Compute", "⚡  حساب"),
    "files.warning": (
        "⚠️  MD5 / SHA-1 sont obsolètes : préférez SHA-256 pour une vérification d'intégrité.",
        "⚠️  MD5 / SHA-1 are obsolete: prefer SHA-256 for integrity checks.",
        "⚠️  MD5 / SHA-1 قديمان: يُفضل SHA-256 للتحقق من السلامة."),
    "files.fingerprint": ("🔑  Empreinte du Fichier", "🔑  File Fingerprint", "🔑  بصمة الملف"),
    "files.no_file": ("Aucun fichier analysé", "No file analyzed", "لم يتم تحليل أي ملف"),
    "files.copy_hash": ("📋  Copier le Hash", "📋  Copy Hash", "📋  نسخ التجزئة"),
    "files.verify": ("🔍  Vérification du Hash", "🔍  Hash Verification", "🔍  التحقق من التجزئة"),
    "files.reference_hint": (
        "Collez le hash de référence (fourni par l'éditeur ou signataire) :",
        "Paste the reference hash (provided by the publisher or signer):",
        "الصق التجزئة المرجعية (التي يوفرها الناشر أو الموقّع):"),
    "files.verify_button": ("🔍  Vérifier l'Intégrité", "🔍  Verify Integrity", "🔍  التحقق من السلامة"),
    "files.file_dialog": ("Sélectionner un fichier", "Select a file", "اختر ملفاً"),
    "files.not_found": ("Fichier introuvable.", "File not found.", "الملف غير موجود."),
    "files.calculating": ("Calcul en cours…", "Computing…", "جارٍ الحساب…"),
    "files.stopped": ("Arrêt demandé…", "Stop requested…", "تم طلب الإيقاف…"),
    "files.done": ("Terminé — {size} octets", "Done — {size} bytes", "اكتمل — {size} بايت"),
    "files.progress": ("{done} / {total} octets", "{done} / {total} bytes", "{done} / {total} بايت"),
    "files.invalidated": ("Empreinte invalidée — recalculez.", "Hash invalidated — recompute.", "أُلغيت البصمة — أعد الحساب."),
    "files.calc_error": ("Erreur lors du calcul", "Computation error", "خطأ أثناء الحساب"),
    "files.compute_first": ("Calculez d'abord le hash du fichier.", "Compute the file hash first.", "احسب تجزئة الملف أولاً."),
    "files.enter_reference": ("Entrez un hash de référence.", "Enter a reference hash.", "أدخل تجزئة مرجعية."),
    "files.invalid_length": ("Hash {algo} invalide : {length} caractères hexadécimaux attendus.", "Invalid {algo} hash: {length} hex characters expected.", "تجزئة {algo} غير صالحة: {length} حرفاً سداسياً مطلوباً."),
    "files.ok": ("✅  INTÉGRITÉ CONFIRMÉE — Les empreintes correspondent", "✅  INTEGRITY CONFIRMED — Hashes match", "✅  سلامة مؤكدة — البصمتان متطابقتان"),
    "files.ko": ("❌  INTÉGRITÉ COMPROMISE — Les empreintes ne correspondent pas !", "❌  INTEGRITY COMPROMISED — Hashes do not match!", "❌  سلامة مخترقة — البصمتان غير متطابقتين!"),
    "log.file_hash": ("Hash Fichier", "File hash", "تجزئة الملف"),
    "log.file_hash.detail": ("{algo} · empreinte calculée ({size} octets)", "{algo} · fingerprint computed ({size} bytes)", "{algo} · تم حساب البصمة ({size} بايت)"),
    "log.verify": ("Vérification Intégrité", "Integrity check", "التحقق من السلامة"),
    "log.match": ("MATCH", "MATCH", "تطابق"),
    "log.mismatch": ("MISMATCH ⚠️", "MISMATCH ⚠️", "عدم تطابق ⚠️"),

    # ── Scanner de ports ───────────────────────────────────────────────────
    "page.scanner.title": ("Scanner de Ports", "Port Scanner", "ماسك المنافذ"),
    "page.scanner.subtitle": (
        "Analysez les ports TCP ouverts d'un hôte (TCP Connect Scan). "
        "Scannez uniquement des cibles que vous êtes autorisé à tester.",
        "Scan open TCP ports on a host (TCP Connect Scan). "
        "Only scan targets you are authorized to test.",
        "افحص منافذ TCP المفتوحة على مضيف (فحص TCP Connect). "
        "افحص فقط الأهداف التي تملك إذناً بفحصها."),
    "scanner.config": ("⚙️  Configuration du Scan", "⚙️  Scan Configuration", "⚙️  إعدادات الفحص"),
    "scanner.host": ("Hôte / IP :", "Host / IP:", "المضيف / IP:"),
    "scanner.start_port": ("Port de début :", "Start port:", "منفذ البداية:"),
    "scanner.end_port": ("Port de fin :", "End port:", "منفذ النهاية:"),
    "scanner.timeout": ("Timeout (s) :", "Timeout (s):", "المهلة (ث):"),
    "scanner.presets": ("Préréglages :", "Presets:", "إعدادات جاهزة:"),
    "scanner.preset.top": ("Top 1024", "Top 1024", "الأكثر شيوعاً 1024"),
    "scanner.preset.web": ("Web", "Web", "ويب"),
    "scanner.preset.extended": ("Étendu", "Extended", "موسّع"),
    "scanner.launch": ("🔍  Lancer le Scan", "🔍  Start Scan", "🔍  بدء الفحص"),
    "scanner.open_ports": ("📋  Ports Ouverts", "📋  Open Ports", "📋  المنافذ المفتوحة"),
    "scanner.invalid_params": ("Paramètres invalides.", "Invalid parameters.", "معلمات غير صالحة."),
    "scanner.invalid_host": ("Hôte invalide (IP ou nom d'hôte attendu).", "Invalid host (IP or hostname expected).", "مضيف غير صالح (IP أو اسم مضيف مطلوب)."),
    "scanner.invalid_range": ("Plage de ports invalide.", "Invalid port range.", "نطاق المنافذ غير صالح."),
    "scanner.invalid_timeout": ("Timeout invalide : choisissez une valeur entre 0,05 et 5 secondes.", "Invalid timeout: choose a value between 0.05 and 5 seconds.", "مهلة غير صالحة: اختر قيمة بين 0.05 و 5 ثوان."),
    "scanner.confirm_large": ("Scanner {count} ports peut prendre du temps. Continuer ?", "Scanning {count} ports may take a while. Continue?", "فحص {count} منفذاً قد يستغرق وقتاً. المتابعة؟"),
    "scanner.started": ("Scan de {host}  |  Ports {start}–{end}  |  Timeout {timeout}s\nDémarré le {date}", "Scan of {host}  |  Ports {start}–{end}  |  Timeout {timeout}s\nStarted on {date}", "فحص {host}  |  المنافذ {start}–{end}  |  المهلة {timeout}ث\nبدأ في {date}"),
    "scanner.stopping": ("Arrêt en cours…", "Stopping…", "جارٍ الإيقاف…"),
    "scanner.error": ("Hôte introuvable : {host} ({error})", "Host not found: {host} ({error})", "المضيف غير موجود: {host} ({error})"),
    "scanner.port_open": (
        "✅  Port {port:5d}   OUVERT   [{svc}]",
        "✅  Port {port:5d}   OPEN   [{svc}]",
        "✅  منفذ {port:5d}   مفتوح   [{svc}]"),
    "scanner.progress": ("{done}/{total} ports scannés", "{done}/{total} ports scanned", "{done}/{total} منفذاً تم فحصها"),
    "scanner.impossible": ("Scan impossible", "Scan failed", "تعذر الفحص"),
    "scanner.aborted": ("⏹  Scan interrompu — {count} port(s) trouvé(s) avant l'arrêt", "⏹  Scan interrupted — {count} port(s) found before stopping", "⏹  تم إيقاف الفحص — تم العثور على {count} منفذ قبل الإيقاف"),
    "scanner.aborted_count": ("{count} port(s) avant arrêt", "{count} port(s) before stop", "{count} منفذ قبل الإيقاف"),
    "scanner.done": ("Scan terminé ✅  —  {count} port(s) ouvert(s) trouvé(s)", "Scan complete ✅  —  {count} open port(s) found", "اكتمل الفحص ✅  —  تم العثور على {count} منفذ مفتوح"),
    "scanner.count": ("{count} port(s) ouvert(s)", "{count} open port(s)", "{count} منفذ مفتوح"),
    "log.scan": ("Scan Ports", "Port scan", "فحص المنافذ"),
    "log.scan.done": ("{host} → {count} port(s) ouvert(s)", "{host} → {count} open port(s)", "{host} → {count} منفذ مفتوح"),
    "log.scan.aborted": ("{host} → interrompu ({count} port(s))", "{host} → interrupted ({count} port(s))", "{host} → أُوقف ({count} منفذ)"),

    # ── Base64 ─────────────────────────────────────────────────────────────
    "page.base64.title": ("Encodeur / Décodeur Base64", "Base64 Encoder / Decoder", "مشفّر / فاكّ Base64"),
    "page.base64.subtitle": ("Encodez et décodez des données en Base64", "Encode and decode Base64 data", "شفّر وفكّ ترميز البيانات بصيغة Base64"),
    "base64.source": ("📝  Texte Source", "📝  Source Text", "📝  النص المصدر"),
    "base64.encode": ("🔒  Encoder →", "🔒  Encode →", "🔒  ترميز →"),
    "base64.decode": ("🔓  ← Décoder", "🔓  ← Decode", "🔓  ← فك ترميز"),
    "base64.swap": ("⇅  Inverser", "⇅  Swap", "⇅  تبديل"),
    "base64.clear": ("🗑️  Tout effacer", "🗑️  Clear all", "🗑️  مسح الكل"),
    "base64.result": ("📤  Résultat", "📤  Result", "📤  النتيجة"),
    "base64.encoded": ("✅  Encodé — {count} caractères", "✅  Encoded — {count} characters", "✅  تم الترميز — {count} حرف"),
    "base64.decoded": ("✅  Décodé — {count} caractères", "✅  Decoded — {count} characters", "✅  تم فك الترميز — {count} حرف"),
    "base64.binary": ("✅  Décodé (binaire non UTF-8) — {count} octets en hexadécimal", "✅  Decoded (non-UTF-8 binary) — {count} bytes in hex", "✅  تم فك الترميز (ثنائي غير UTF-8) — {count} بايت بالنظام الست عشري"),
    "base64.invalid": ("❌  Données Base64 invalides", "❌  Invalid Base64 data", "❌  بيانات Base64 غير صالحة"),
    "log.b64_encode": ("Encodage Base64", "Base64 encoding", "ترميز Base64"),
    "log.b64_encode.detail": ("{src} → {out} chars", "{src} → {out} chars", "{src} → {out} حرف"),
    "log.b64_decode": ("Décodage Base64", "Base64 decoding", "فك ترميز Base64"),

    # ── Réseau ─────────────────────────────────────────────────────────────
    "page.network.title": ("Informations Réseau", "Network Information", "معلومات الشبكة"),
    "page.network.subtitle": ("Informations locales, résolution DNS et test de connectivité", "Local information, DNS resolution and connectivity test", "معلومات محلية، حل DNS واختبار الاتصال"),
    "network.refresh": ("🔄  Actualiser", "🔄  Refresh", "🔄  تحديث"),
    "network.local": ("💻  Informations Locales", "💻  Local Information", "💻  معلومات محلية"),
    "network.dns": ("🔍  Résolution DNS", "🔍  DNS Resolution", "🔍  حل DNS"),
    "network.resolve": ("🔍  Résoudre", "🔍  Resolve", "🔍  حل"),
    "network.ping": ("📡  Test de Connectivité (Ping)", "📡  Connectivity Test (Ping)", "📡  اختبار الاتصال (Ping)"),
    "network.ping_button": ("📡  Ping", "📡  Ping", "📡  بينغ"),
    "network.hostname": ("Hostname", "Hostname", "اسم المضيف"),
    "network.local_ip": ("Adresse IP locale", "Local IP address", "عنوان IP المحلي"),
    "network.os": ("OS", "OS", "نظام التشغيل"),
    "network.python": ("Python", "Python", "بايثون"),
    "dns.invalid": ("❌  Nom de domaine invalide", "❌  Invalid domain name", "❌  اسم نطاق غير صالح"),
    "dns.resolving": ("⏳  Résolution de {domain}…", "⏳  Resolving {domain}…", "⏳  جارٍ حل {domain}…"),
    "dns.error": ("❌  Erreur : {error}", "❌  Error: {error}", "❌  خطأ: {error}"),
    "dns.no_ipv4": ("❌  Aucune adresse IPv4 pour {domain}", "❌  No IPv4 address for {domain}", "❌  لا يوجد عنوان IPv4 لـ {domain}"),
    "dns.ok": ("✅  {domain}  →  {ip}", "✅  {domain}  →  {ip}", "✅  {domain}  →  {ip}"),
    "dns.invalid_host": ("❌  Hôte invalide", "❌  Invalid host", "❌  مضيف غير صالح"),
    "ping.running": ("⏳  Ping en cours...", "⏳  Ping in progress...", "⏳  البينغ جارٍ..."),
    "ping.accessible": ("accessible", "reachable", "متصل"),
    "ping.unreachable": ("inaccessible", "unreachable", "غير متصل"),
    "ping.result": ("{mark}  {host} est {state}", "{mark}  {host} is {state}", "{mark}  {host} {state}"),
    "log.dns": ("Résolution DNS", "DNS resolution", "حل DNS"),
    "log.dns.detail": ("{domain} → {ip}", "{domain} → {ip}", "{domain} → {ip}"),
    "log.ping": ("Ping", "Ping", "بينغ"),
    "log.ping.detail": ("{host}: {state}", "{host}: {state}", "{host}: {state}"),

    # ── Journal ────────────────────────────────────────────────────────────
    "page.logs.title": ("Journal d'Activité", "Activity Log", "سجل النشاط"),
    "page.logs.subtitle": ("Historique de toutes les actions effectuées dans l'application", "History of all actions performed in the application", "سجل جميع الإجراءات المنفذة في التطبيق"),
    "logs.export": ("💾  Exporter", "💾  Export", "💾  تصدير"),
    "logs.clear": ("🗑️  Effacer", "🗑️  Clear", "🗑️  مسح"),
    "logs.entries": ("{count} entrée(s)", "{count} entry(ies)", "{count} إدخال"),
    "logs.empty": ("Aucune activité enregistrée.", "No activity recorded.", "لا يوجد نشاط مسجل."),
    "logs.clear_confirm": ("Effacer tout le journal ?", "Clear the whole log?", "مسح السجل بالكامل؟"),
    "logs.no_logs": ("Aucun log à exporter.", "No log to export.", "لا يوجد سجل للتصدير."),
    "logs.export_dialog": ("Exporter le journal", "Export the log", "تصدير السجل"),
    "logs.export_filter": ("Fichiers texte (*.txt);;Tous les fichiers (*.*)", "Text files (*.txt);;All files (*.*)", "ملفات نصية (*.txt);;كل الملفات (*.*)"),
    "logs.export_header": ("=== {app} — Activity Log ===\n\n", "=== {app} — Activity Log ===\n\n", "=== {app} — سجل النشاط ===\n\n"),
    "logs.export_error": ("Export impossible :\n{error}", "Export failed:\n{error}", "تعذر التصدير:\n{error}"),
    "logs.export_ok": ("Journal sauvegardé :\n{path}\n\n(Fichier texte non chiffré.)", "Log saved:\n{path}\n\n(Unencrypted text file.)", "تم حفظ السجل:\n{path}\n\n(ملف نصي غير مشفر.)"),
    "logs.exported": ("Exporté !", "Exported!", "تم التصدير!"),

    # ── Fermeture ──────────────────────────────────────────────────────────
    "quit.question": ("Voulez-vous vraiment quitter l'application ?", "Do you really want to quit the application?", "هل تريد فعلاً إنهاء التطبيق؟"),
    "quit.busy": ("Une opération est en cours (scan, ping ou hachage de fichier) : quitter maintenant l'interrompra.\nToutes les données non sauvegardées seront perdues.", "An operation is in progress (scan, ping or file hashing): quitting now will interrupt it.\nAll unsaved data will be lost.", "توجد عملية جارية (فحص، بينغ أو تجزئة ملف): الخروج الآن سيوقفها.\nستضيع جميع البيانات غير المحفوظة."),

    # ── Divers ─────────────────────────────────────────────────────────────
    "log.ok": ("OK", "OK", "حسناً"),
    "msg.result_copied": ("Résultat copié dans le presse-papiers.", "Result copied to clipboard.", "تم نسخ النتيجة إلى الحافظة."),
    "msg.file_hash_copied": ("Hash copié dans le presse-papiers.", "Hash copied to clipboard.", "تم نسخ التجزئة إلى الحافظة."),
    "msg.password_copied": ("Mot(s) de passe copié(s) dans le presse-papiers.", "Password(s) copied to clipboard.", "تم نسخ كلمة المرور (كلمات المرور) إلى الحافظة."),

    # ── Capture d'écran ────────────────────────────────────────────────────
    "capture.dialog_title": ("Enregistrer la capture", "Save screenshot", "حفظ لقطة الشاشة"),
    "capture.filter": ("Images PNG (*.png)", "PNG images (*.png)", "صور PNG (*.png)"),
    "capture.error": ("Impossible d'enregistrer la capture.", "Could not save the screenshot.", "تعذر حفظ لقطة الشاشة."),
    "log.capture": ("Capture écran", "Screenshot", "لقطة شاشة"),
    "log.capture.done": ("Capture enregistrée : {file}", "Screenshot saved: {file}", "تم حفظ لقطة الشاشة: {file}"),

    # ── Mise à jour ─────────────────────────────────────────────────────────
    "nav.update": ("🆕  Mise à jour", "🆕  Update", "🆕  التحديث"),
    "page.update.title": ("Mise à jour", "Update", "التحديث"),
    "page.update.subtitle": ("Recherchez une nouvelle version et téléchargez l'artefact adapté à votre installation.", "Check for a new release and download the right artifact for your installation.", "ابحث عن إصدار جديد ونزّل الملف المناسب لتثبيتك."),
    "update.mode": ("Mode d'installation", "Installation mode", "وضع التثبيت"),
    "update.mode.portable": ("Portable (archive ZIP)", "Portable (ZIP archive)", "محمول (أرشيف ZIP)"),
    "update.mode.installer": ("Installateur Windows", "Windows installer", "مثبّت ويندوز"),
    "update.mode.pip": ("Paquet Python (pip)", "Python package (pip)", "حزمة بايثون (pip)"),
    "update.installed": ("Version installée", "Installed version", "الإصدار المثبّت"),
    "update.last_check": ("Dernière vérification", "Last check", "آخر فحص"),
    "update.never": ("Jamais", "Never", "لم يسبق"),
    "update.auto_check": ("Vérifier au démarrage (une fois par jour)", "Check at startup (once a day)", "الفحص عند التشغيل (مرة واحدة يومياً)"),
    "update.check_button": ("Vérifier maintenant", "Check now", "تحقق الآن"),
    "update.checking": ("Recherche d'une nouvelle version…", "Looking for a new version…", "جارٍ البحث عن إصدار جديد…"),
    "update.up_to_date": ("Vous utilisez la dernière version.", "You are running the latest version.", "أنت تستخدم أحدث إصدار."),
    "update.available": ("Version disponible", "Available version", "الإصدار المتاح"),
    "update.available_detail": ("Une nouvelle version est disponible : {version}.", "A new version is available: {version}.", "إصدار جديد متاح: {version}."),
    "update.notes": ("Notes de version", "Release notes", "ملاحظات الإصدار"),
    "update.no_notes": ("Aucune note fournie.", "No release notes provided.", "لا توجد ملاحظات."),
    "update.download_button": ("Télécharger la mise à jour", "Download update", "تنزيل التحديث"),
    "update.open_release": ("Ouvrir la page Release", "Open release page", "فتح صفحة الإصدار"),
    "update.copy_command": ("Copier la commande", "Copy command", "نسخ الأمر"),
    "update.pip_hint": ("Mettez à jour depuis un terminal avec la commande ci-dessous.", "Update from a terminal with the command below.", "حدّث من الطرفية باستخدام الأمر أدناه."),
    "update.downloading": ("Téléchargement… {percent} %", "Downloading… {percent}%", "جارٍ التنزيل… {percent}٪"),
    "update.downloaded": ("Téléchargement terminé : {file}", "Download finished: {file}", "اكتمل التنزيل: {file}"),
    "update.verified": ("Empreinte SHA-256 vérifiée.", "SHA-256 checksum verified.", "تم التحقق من بصمة SHA-256."),
    "update.unverified": ("Aucune empreinte publiée pour cet artefact : fichier reçu via HTTPS.", "No checksum published for this artifact: file received over HTTPS.", "لا بصمة منشورة لهذا الملف: تم استلامه عبر HTTPS."),
    "update.portable_ready": ("Nouvelle version extraite dans :\n{path}\n\nFermez cette fenêtre, puis relancez l'application depuis le nouveau dossier.", "New version extracted to:\n{path}\n\nClose this window, then restart the application from the new folder.", "تم استخراج الإصدار الجديد في:\n{path}\n\nأغلق هذه النافذة، ثم أعد تشغيل التطبيق من المجلد الجديد."),
    "update.installer_confirm": ("L'installateur a été téléchargé :\n{path}\n\nLe lancer maintenant ?", "The installer has been downloaded:\n{path}\n\nLaunch it now?", "تم تنزيل المثبّت:\n{path}\n\nهل تريد تشغيله الآن؟"),
    "update.open_folder": ("Ouvrir le dossier", "Open folder", "فتح المجلد"),
    "update.security": ("Sécurité", "Security", "الأمان"),
    "update.security_detail": ("Connexion HTTPS uniquement. Le téléchargement est annulé si l'empreinte SHA-256 publiée ne correspond pas. Rien n'est installé sans votre accord.", "HTTPS only. The download is aborted if the published SHA-256 checksum does not match. Nothing is installed without your approval.", "اتصال HTTPS فقط. يُلغى التنزيل إذا لم تطابق بصمة SHA-256 المنشورة. لا يُثبَّت أي شيء دون موافقتك."),
    "update.error.network": ("Connexion impossible :\n{error}", "Could not connect:\n{error}", "تعذر الاتصال:\n{error}"),
    "update.error.http": ("Erreur HTTP {code}.", "HTTP error {code}.", "خطأ HTTP {code}."),
    "update.error.json": ("Réponse GitHub illisible.", "Could not read GitHub's response.", "تعذرت قراءة استجابة GitHub."),
    "update.error.version": ("Version inattendue : {value}", "Unexpected version: {value}", "إصدار غير متوقع: {value}"),
    "update.error.https": ("URL non sécurisée refusée.", "Insecure URL rejected.", "تم رفض رابط غير آمن."),
    "update.error.size": ("Fichier trop volumineux.", "File too large.", "الملف كبير جداً."),
    "update.error.checksum": ("Empreinte SHA-256 invalide : téléchargement supprimé.", "Invalid SHA-256 checksum: download discarded.", "بصمة SHA-256 غير صالحة: تم حذف التنزيل."),
    "update.error.cancelled": ("Téléchargement annulé.", "Download cancelled.", "تم إلغاء التنزيل."),
    "update.error.asset": ("Aucun artefact compatible avec ce mode d'installation.", "No artifact matching this installation mode.", "لا يوجد ملف متوافق مع وضع التثبيت هذا."),
    "update.error.extract": ("Archive invalide ou chemin non sûr.", "Invalid archive or unsafe path.", "أرشيف غير صالح أو مسار غير آمن."),
    "log.update.check": ("Vérification des mises à jour", "Update check", "فحص التحديثات"),
    "log.update.check.detail": ("Version disponible : {version}", "Available version: {version}", "الإصدار المتاح: {version}"),
    "log.update.download": ("Mise à jour téléchargée", "Update downloaded", "تم تنزيل التحديث"),
    "log.update.download.detail": ("Fichier : {file} — {checksum}", "File: {file} — {checksum}", "الملف: {file} — {checksum}"),
}


class I18n:
    """État linguistique global et moteur de traduction."""

    def __init__(self, language="fr"):
        self.language = language if language in LANGUAGES else "fr"

    @property
    def direction(self):
        """Sens d'écriture, utilisé pour basculer l'interface en RTL."""
        return "rtl" if self.language == "ar" else "ltr"

    def tr(self, key, **kwargs):
        """Traduit ``key`` dans la langue courante en substituant ``kwargs``."""
        values = STRINGS.get(key)
        if values is None:
            return key
        text = values[LANG_INDEX.get(self.language, 0)]
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError, IndexError):
                return text
        return text

    def set_language(self, code):
        if code in LANGUAGES:
            self.language = code


I18N = I18n()


def tr(key, **kwargs):
    """Raccourci vers :meth:`I18n.tr`."""
    return I18N.tr(key, **kwargs)


# Catalogues Qt fournis par PySide6. ``qtbase`` couvre Qt Widgets (boîtes de
# dialogue, boutons standard) ; ``qt`` regroupe les autres modules Qt.
_QT_CATALOGS = ("qtbase_{lang}", "qt_{lang}")
_QT_TRANSLATORS: list[QTranslator] = []


def install_qt_translator(language):
    """Applique les traductions Qt pour ``language`` et renvoie ``True`` si
    au moins un catalogue a été chargé.

    Les fichiers ``.qm`` sont lus depuis ``QLibraryInfo.TranslationsPath``, le
    chemin par défaut de Qt (également présent dans l'exécutable PyInstaller).
    L'anglais étant la langue native de Qt, les traducteurs précédents sont
    simplement retirés. Les objets ``QTranslator`` doivent rester vivants tant
    qu'ils sont installés : ils sont donc conservés dans ``_QT_TRANSLATORS``.

    Sans application Qt active (ex. : import dans un test unitaire), la
    fonction ne fait rien et renvoie ``False``.
    """
    app = QCoreApplication.instance()
    if app is None:
        return False

    for old in _QT_TRANSLATORS:
        app.removeTranslator(old)
    _QT_TRANSLATORS.clear()

    if language == "en":
        return False

    translations_dir = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    loaded = False
    for catalog in _QT_CATALOGS:
        translator = QTranslator(app)
        if translator.load(catalog.format(lang=language), translations_dir):
            app.installTranslator(translator)
            _QT_TRANSLATORS.append(translator)
            loaded = True
    return loaded
