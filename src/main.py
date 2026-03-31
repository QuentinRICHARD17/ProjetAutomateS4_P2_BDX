import os


class Automate:
    def __init__(self):
        self.alphabet = []
        self.nb_etats = 0
        self.etats = []  # Nouvelle liste pour stocker les noms réels des états (ex: 0, 1, 2, 'P')
        self.initials = set()
        self.terminals = set()
        self.transitions = {}

    def lire_fichier(self, num_automate):
        nom_fichier = f"../AutomatesTXT/{num_automate}.txt"
        if not os.path.exists(nom_fichier):
            print(f"Erreur : Le fichier {nom_fichier} est introuvable.")
            return False

        try:
            with open(nom_fichier, 'r') as f:
                lignes = [l.strip() for l in f.readlines() if l.strip()]

                # Fonction utilitaire pour lire un état (entier ou 'P')
                def parse_etat(val):
                    return 'P' if val == 'P' else int(val)

                nb_symboles = int(lignes[0])
                self.alphabet = [chr(97 + i) for i in range(nb_symboles)]
                self.nb_etats = int(lignes[1])

                parts_init = lignes[2].split()
                self.initials = set(map(parse_etat, parts_init[1:]))

                parts_term = lignes[3].split()
                self.terminals = set(map(parse_etat, parts_term[1:]))

                nb_trans = int(lignes[4])
                trans_data = []
                has_poubelle = False

                # Lecture préalable des transitions pour repérer 'P'
                for i in range(5, 5 + nb_trans):
                    t = lignes[i]

                    if t.startswith('P'):
                        dep = 'P'
                        idx = 1
                    else:
                        dep_str = ""
                        idx = 0
                        while idx < len(t) and t[idx].isdigit():
                            dep_str += t[idx]
                            idx += 1
                        dep = int(dep_str)

                    sym = t[idx]

                    arr_str = t[idx + 1:]
                    arr = 'P' if arr_str == 'P' else int(arr_str)

                    if dep == 'P' or arr == 'P':
                        has_poubelle = True

                    trans_data.append((dep, sym, arr))

                # Construction de la liste des états
                if has_poubelle:
                    # 'P' remplace le dernier état numérique
                    self.etats = list(range(self.nb_etats - 1)) + ['P']
                else:
                    self.etats = list(range(self.nb_etats))

                # Initialisation des transitions
                self.transitions = {i: {s: set() for s in self.alphabet + ['e']} for i in self.etats}

                # Remplissage
                for dep, sym, arr in trans_data:
                    self.transitions[dep][sym].add(arr)

            return True
        except Exception as e:
            print(f"Erreur de lecture : {e}")
            return False

    def afficher(self, titre="Automate"):
        print(f"\n--- {titre} ---")
        header = "État | " + " | ".join(f"  {s}  " for s in self.alphabet)
        print("-" * len(header))
        print(header)
        print("-" * len(header))

        for i in self.etats:
            prefix = ""
            if i in self.initials: prefix += "E"
            if i in self.terminals: prefix += "S"
            # str(i) permet d'afficher 'P' proprement
            row = f"{prefix:2}{str(i):2} | "
            cells = []
            for s in self.alphabet:
                dest = self.transitions[i].get(s, set())
                cells.append(",".join(map(str, sorted(list(dest), key=str))) if dest else " - ")
            print(row + " | ".join(f"{c:5}" for c in cells))
        print("-" * len(header))

    # --- DIAGNOSTICS ---

    def est_deterministe(self):
        if len(self.initials) != 1:
            return False, "Plusieurs états initiaux."
        for i in self.etats:
            if self.transitions[i].get('e'): return False, "Contient des transitions epsilon."
            for s in self.alphabet:
                if len(self.transitions[i].get(s, set())) > 1:
                    return False, f"Transition multiple pour l'état {i} sur '{s}'."
        return True, ""

    def est_complet(self):
        for i in self.etats:
            for s in self.alphabet:
                if not self.transitions[i].get(s, set()):
                    return False, f"Manque transition pour '{s}' à l'état {i}."
        return True, ""

    def est_standard(self):
        if len(self.initials) != 1: return False, "Pas d'état initial unique."
        ini = list(self.initials)[0]
        for i in self.etats:
            for s in self.alphabet:
                if ini in self.transitions[i].get(s, set()):
                    return False, f"Une transition revient sur l'état initial {ini}."
        return True, ""

    # --- TRANSFORMATIONS ---

    def standardiser(self):
        # On cherche un nom de nouvel état numérique qui n'existe pas encore
        n_ini = 0
        while n_ini in self.etats:
            n_ini += 1

        self.etats.append(n_ini)
        self.transitions[n_ini] = {s: set() for s in self.alphabet + ['e']}

        for i in self.initials:
            for s in self.alphabet:
                self.transitions[n_ini][s].update(self.transitions[i][s])
            if i in self.terminals: self.terminals.add(n_ini)

        self.initials = {n_ini}
        self.nb_etats += 1
        print("Standardisation terminée.")

    def epsilon_closure(self, etats):
        closure = set(etats)
        stack = list(etats)
        while stack:
            u = stack.pop()
            for v in self.transitions[u].get('e', set()):
                if v not in closure:
                    closure.add(v)
                    stack.append(v)
        return closure

    def determiniser_et_completer(self):
        start_set = tuple(sorted(list(self.epsilon_closure(self.initials)), key=str))
        states_map = {start_set: 0}
        queue = [start_set]
        new_trans = {}
        new_terminals = set()

        idx = 0
        while idx < len(queue):
            curr_tuple = queue[idx]
            new_trans[idx] = {s: set() for s in self.alphabet}

            if curr_tuple != ("P",) and any(s in self.terminals for s in curr_tuple):
                new_terminals.add(idx)

            for s in self.alphabet:
                if curr_tuple == ("P",):
                    new_trans[idx][s].add(idx)
                    continue

                reach = set()
                for sub in curr_tuple:
                    reach.update(self.transitions[sub].get(s, set()))

                next_set = tuple(sorted(list(self.epsilon_closure(reach)), key=str))
                if not next_set:
                    next_set = ("P",)

                if next_set not in states_map:
                    states_map[next_set] = len(queue)
                    queue.append(next_set)
                new_trans[idx][s].add(states_map[next_set])
            idx += 1

        print("\nCorrespondance des nouveaux états :")
        for t, i in states_map.items():
            nom = "Poubelle" if t == ("P",) else f"{{{'.'.join(map(str, t))}}}"
            print(f"État {i} = {nom}")

        self.nb_etats = len(queue)
        self.etats = list(range(self.nb_etats))  # Le nouvel automate AFD a des états 0..N
        self.initials = {0}
        self.terminals = new_terminals
        self.transitions = new_trans

    def minimiser(self):
        if not self.est_complet()[0]: self.determiniser_et_completer()

        groups = []
        g_term = tuple(sorted(list(self.terminals), key=str))
        g_non_term = tuple(sorted([i for i in self.etats if i not in self.terminals], key=str))

        if g_term: groups.append(g_term)
        if g_non_term: groups.append(g_non_term)

        step = 0
        while True:
            print(f"P{step}: {groups}")
            mapping = {e: i for i, g in enumerate(groups) for e in g}
            new_groups_dict = {}
            for g in groups:
                for e in g:
                    sig = (mapping[e],) + tuple(mapping[list(self.transitions[e][s])[0]] for s in self.alphabet)
                    if sig not in new_groups_dict: new_groups_dict[sig] = []
                    new_groups_dict[sig].append(e)

            next_groups = [tuple(sorted(v, key=str)) for v in new_groups_dict.values()]
            next_groups.sort(key=str)
            if len(next_groups) == len(groups): break
            groups = next_groups
            step += 1
        print("Minimisation terminée.")
        # --- NOUVELLE PARTIE : RECONSTRUCTION ---
        # 1. On crée un dictionnaire pour savoir dans quel nouveau groupe va chaque ancien état
        etat_vers_groupe = {e: i for i, g in enumerate(groups) for e in g}

        # 2. On met à jour les infos de base
        self.nb_etats = len(groups)
        self.etats = list(range(self.nb_etats))

        # 3. On met à jour les initiaux et terminaux avec leurs nouveaux numéros
        self.initials = {etat_vers_groupe[e] for e in self.initials}
        self.terminals = {etat_vers_groupe[e] for e in self.terminals}

        # 4. On reconstruit les transitions
        nouvelles_transitions = {i: {s: set() for s in self.alphabet} for i in self.etats}

        for i, groupe in enumerate(groups):
            # On prend un état au hasard dans le groupe (le premier) car ils ont tous le même comportement
            representant = groupe[0]
            for s in self.alphabet:
                ancienne_dest = list(self.transitions[representant][s])[0]
                nouvelle_dest = etat_vers_groupe[ancienne_dest]
                nouvelles_transitions[i][s].add(nouvelle_dest)

        self.transitions = nouvelles_transitions

        # Affichage pour montrer à l'examinateur la correspondance
        print("\nCorrespondance des états minimisés :")
        for i, g in enumerate(groups):
            print(f"Nouvel état {i} = anciens états {{{'.'.join(map(str, g))}}}")

    def complement(self):
        if not self.est_deterministe()[0] or not self.est_complet()[0]:
            print("L'automate doit être AFD et Complet.")
            return
        self.terminals = {i for i in self.etats if i not in self.terminals}
        print("Automate complémentaire généré.")


def menu():
    while True:
        print("\n" + "=" * 40)
        choix = input("Numéro d'automate (01-44) ou 'q' pour quitter : ")
        if choix.lower() == 'q': break

        af = Automate()
        if af.lire_fichier(choix):
            af.afficher("Initial")

            std, msg = af.est_standard()
            print(f"Standard : {std} ({msg})")
            if not std and input("Standardiser ? (o/n) : ").lower() == 'o':
                af.standardiser()
                af.afficher("Standardisé")

            det, msg_det = af.est_deterministe()
            comp, msg_comp = af.est_complet()
            print(f"Déterministe : {det} ({msg_det})")
            print(f"Complet : {comp} ({msg_comp})")

            if not det or not comp:
                print("Déterminisation et Complétion...")
                af.determiniser_et_completer()
                af.afficher("AFD Complet")

            if input("Minimiser ? (o/n) : ").lower() == 'o':
                af.minimiser()
                af.afficher("Minimal")

            if input("Complémentaire ? (o/n) : ").lower() == 'o':
                af.complement()
                af.afficher("Complémentaire")

            while True:
                mot = input("Mot à tester (ou 'fin') : ")
                if mot == 'fin': break
                curr = list(af.initials)[0]
                possible = True
                for c in mot:
                    if c in af.alphabet:
                        curr = list(af.transitions[curr][c])[0]
                    else:
                        possible = False;
                        break
                print(f"Reconnu : {'OUI' if possible and curr in af.terminals else 'NON'}")


if __name__ == "__main__":
    menu()