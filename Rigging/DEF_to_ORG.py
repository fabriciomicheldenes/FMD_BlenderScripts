import bpy

# ----------------------------
# Config
# ----------------------------
DEF_PREFIX = "DEF-"
ORG_PREFIX = "ORG-"

DEF_ROOT_COLL_NAME = "DEF"
ORG_ROOT_COLL_NAME = "ORG"

# Se já existir ORG na armature original, usamos este fallback para evitar colisão
ORG_ROOT_FALLBACK = "ORG__DUP"

# ----------------------------
# Utilities
# ----------------------------

def require_active_armature_object():
    obj = bpy.context.object
    if obj is None or obj.type != "ARMATURE":
        raise RuntimeError("Selecione uma Armature (objeto do tipo ARMATURE) antes de rodar.")
    return obj

def set_object_mode():
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode='OBJECT')

def set_edit_mode():
    if bpy.context.mode != "EDIT_ARMATURE":
        bpy.ops.object.mode_set(mode='EDIT')

def set_pose_mode():
    if bpy.context.mode != "POSE":
        bpy.ops.object.mode_set(mode='POSE')

def duplicate_armature_object_with_data(src_obj: bpy.types.Object) -> bpy.types.Object:
    """
    Duplica o objeto e também o Armature Data (src_obj.data.copy()).
    Linka no mesmo Collection da cena do objeto original.
    """
    set_object_mode()

    dup_obj = src_obj.copy()
    dup_obj.data = src_obj.data.copy()
    dup_obj.animation_data_clear()

    # Linka no mesmo collection (primeiro collection do original)
    if src_obj.users_collection:
        src_obj.users_collection[0].objects.link(dup_obj)
    else:
        bpy.context.scene.collection.objects.link(dup_obj)

    dup_obj.name = f"{src_obj.name}__ORG_SRC"
    dup_obj.data.name = f"{src_obj.data.name}__ORG_SRC"

    return dup_obj



def rename_def_to_org_in_duplicate(dup_obj: bpy.types.Object,
                                   def_prefix=DEF_PREFIX,
                                   org_prefix=ORG_PREFIX,
                                   def_root=DEF_ROOT_COLL_NAME):
    """
    Na armature duplicada:
    - renomeia bones DEF- -> ORG-
    - desabilita deform
    - renomeia bone collections: DEF -> ORG e DEF-* -> ORG-*
    """
    set_object_mode()
    bpy.context.view_layer.objects.active = dup_obj
    dup_obj.select_set(True)

    # --- Rename Bone Collections (Blender 4.x)
    rename_collections(dup_obj)

    # --- Rename Bones (Edit Mode)
    set_edit_mode()
    eb = dup_obj.data.edit_bones

    # 1) Renomeia todos DEF- para ORG- garantindo unicidade
    for b in list(eb):
        if b.name.startswith(def_prefix):
            suffix = b.name[len(def_prefix):]
            new_name = org_prefix + suffix

            # garante que não exista (na armature duplicada)
            if new_name in eb and eb[new_name] != b:
                # evita renome automático .001
                base = new_name + "__SRC"
                i = 0
                candidate = base
                while candidate in eb:
                    i += 1
                    candidate = f"{base}_{i}"
                new_name = candidate

            b.name = new_name

        # 2) Desabilita deform para todos (na duplicada queremos ORG “mecânico”)
        b.use_deform = False

    set_object_mode()

def join_armatures_keep_original(original_obj: bpy.types.Object, dup_obj: bpy.types.Object) -> bpy.types.Object:
    """
    Junta dup_obj dentro de original_obj. O original permanece como objeto final.
    """
    set_object_mode()

    bpy.ops.object.select_all(action='DESELECT')
    original_obj.select_set(True)
    dup_obj.select_set(True)
    bpy.context.view_layer.objects.active = original_obj

    bpy.ops.object.join()  # dup_obj desaparece, bones entram no original
    return original_obj

def add_copy_transforms_constraints(arm_obj: bpy.types.Object,
                                   def_prefix=DEF_PREFIX,
                                   org_prefix=ORG_PREFIX,
                                   owner_space='POSE',
                                   target_space='POSE'):
    """
    Para cada bone DEF-XXX:
    cria constraint COPY_TRANSFORMS apontando para ORG-XXX (mesma armature).
    """
    set_object_mode()
    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.select_set(True)

    set_pose_mode()
    pb = arm_obj.pose.bones

    count = 0
    missing = []

    for name, pbone in pb.items():
        if not name.startswith(def_prefix):
            continue

        suffix = name[len(def_prefix):]
        org_name = org_prefix + suffix

        if org_name not in pb:
            missing.append((name, org_name))
            continue

        # evita duplicar constraints se rodar mais de uma vez
        already = any(c.type == 'COPY_TRANSFORMS' and c.subtarget == org_name for c in pbone.constraints)
        if already:
            continue

        c = pbone.constraints.new(type='COPY_TRANSFORMS')
        c.name = f"CT__{org_name}"
        c.target = arm_obj
        c.subtarget = org_name
        c.owner_space = owner_space
        c.target_space = target_space

        count += 1

    set_object_mode()

    print(f"[OK] Copy Transforms adicionados em {count} bones DEF-*.")
    if missing:
        print("[WARN] Alguns DEF-* não encontraram ORG correspondente:")
        for d, o in missing[:20]:
            print(f"  - {d} -> (faltando) {o}")
        if len(missing) > 20:
            print(f"  ... e mais {len(missing)-20}.")


# ----------------------------
# Orchestrator
# ----------------------------

def rename_collections(dup):
    
    # Seleciona e ativa a nova armature
    set_object_mode()
    bpy.context.view_layer.objects.active = dup
    dup.select_set(True)
    
    root_coll = dup.data.collections.get("DEF")
    for ch in list(root_coll.children):
        if ch.name.startswith("DEF"):
                suffix = ch.name[len("DEF"):]
                target = "ORG" + suffix
                ch.name = target
        print(ch)
        
 
    suffix = root_coll.name[len("DEF"):]
    target = "ORG" + suffix
    root_coll.name = target
    print(root_coll)
    
import bpy

def cleaning_non_DEF(dup,
                     def_root_name="DEF",
                     def_bone_prefix="DEF-"):
    """
    Remove da armature duplicada:
    - Todos os bones que NÃO começam com DEF-
    - Todas as bone collections que NÃO são a raiz DEF nem estão sob a árvore DEF

    Observações:
    - Remove bones em Edit Mode.
    - Remove bone collections via armature.data.collections.
    """

    # --- garante que estamos operando na duplicada ---
    if dup is None or dup.type != "ARMATURE":
        raise RuntimeError("cleaning_non_DEF: objeto inválido (precisa ser ARMATURE).")

    # ativa duplicada
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    dup.select_set(True)
    bpy.context.view_layer.objects.active = dup

    arm = dup.data

    # -----------------------------
    # 1) Coletar árvore de collections sob DEF
    # -----------------------------
    def_root = arm.collections.get(def_root_name)
    if def_root is None:
        raise RuntimeError(f"Não encontrei a Bone Collection raiz '{def_root_name}' na duplicada.")

    keep_colls = set()

    def walk_coll(c):
        keep_colls.add(c)
        for ch in c.children:
            walk_coll(ch)

    walk_coll(def_root)

    # -----------------------------
    # 2) Remover bones que não são DEF-
    # -----------------------------
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.edit_bones

    to_remove = [b for b in eb if not b.name.startswith(def_bone_prefix)]

    # remove com segurança
    for b in to_remove:
        eb.remove(b)

    bpy.ops.object.mode_set(mode='OBJECT')

    # -----------------------------
    # 3) Remover bone collections fora de DEF-tree
    # -----------------------------
    # Importante: remover folhas primeiro para evitar problemas de dependência
    # Vamos ordenar por "profundidade" estimada: removemos collections sem filhos primeiro.
    all_colls = list(arm.collections)

    # lista de remoção = tudo que não está em keep_colls
    remove_colls = [c for c in all_colls if c not in keep_colls]

    # remove em loop: sempre remove as que não têm filhos (ou cujos filhos já foram removidos)
    # para evitar erro de "collection has children".
    removed_any = True
    while removed_any and remove_colls:
        removed_any = False
        for c in list(remove_colls):
            # se ainda tiver filhos, pula por enquanto
            if len(c.children) > 0:
                continue
            # se não tem filhos, remove
            arm.collections.remove(c)
            remove_colls.remove(c)
            removed_any = True

    # se sobrou algo (caso raro), forçamos reparent para soltar e remover
    if remove_colls:
        for c in remove_colls:
            # Solta do parent e remove filhos (fallback agressivo)
            for ch in list(c.children):
                ch.parent = None
            c.parent = None
        # tenta remover novamente
        for c in list(remove_colls):
            if len(c.children) == 0:
                arm.collections.remove(c)

    print(f"[OK] cleaning_non_DEF: removidos {len(to_remove)} bones não-DEF e limpas collections fora de '{def_root_name}'.")
   
def create_mch_collections_from_def(
    arm_obj,
    def_root_name="DEF",
    mch_root_name="MCH",
    def_prefix="DEF-",
    mch_prefix="MCH-"
):
    """
    Cria a árvore de Bone Collections MCH espelhando DEF.
    Não cria nem move bones.
    """

    arm = arm_obj.data

    # ----------------------------
    # helpers
    # ----------------------------
    def get_collection(name):
        return arm.collections.get(name)

    def get_or_create_collection(name, parent=None):
        c = get_collection(name)
        if c is None:
            c = arm.collections.new(name, parent=parent)
        else:
            # força parent correto
            if parent is not None and c.parent != parent:
                c.parent = parent
        return c

    # ----------------------------
    # valida raiz DEF
    # ----------------------------
    def_root = get_collection(def_root_name)
    if def_root is None:
        raise RuntimeError(f"Collection raiz '{def_root_name}' não encontrada.")

    # ----------------------------
    # cria raiz MCH
    # ----------------------------
    mch_root = get_or_create_collection(mch_root_name, parent=None)

    # ----------------------------
    # recursão DEF -> MCH
    # ----------------------------
    def walk(def_coll, mch_parent):
        for ch in def_coll.children:

            # só espelha collections DEF-*
            if not ch.name.startswith(def_prefix):
                continue

            suffix = ch.name[len(def_prefix):]      # Arm.L, Leg.R, etc
            mch_name = mch_prefix + suffix

            mch_coll = get_or_create_collection(mch_name, parent=mch_parent)

            # recursão
            walk(ch, mch_coll)

    walk(def_root, mch_root)

    print("[OK] Estrutura MCH criada com base em DEF.")
    
        
def make_org_from_def_by_duplicate_join_and_constrain():
    original = require_active_armature_object()

    create_mch_collections_from_def(
    arm_obj=original,
    def_root_name="DEF",
    mch_root_name="MCH")
    
    # 1) duplicar
    dup = duplicate_armature_object_with_data(original)
    
    #limpar o que não for DEF-
    cleaning_non_DEF(dup)
    

    # 2) renomear DEF->ORG na duplicada
    rename_def_to_org_in_duplicate(
        dup_obj=dup,
        def_prefix=DEF_PREFIX,
        org_prefix=ORG_PREFIX,
        def_root=DEF_ROOT_COLL_NAME
    )

    # 3) join
    joined = join_armatures_keep_original(original, dup)

    # 4) constraints DEF -> ORG
    add_copy_transforms_constraints(joined, DEF_PREFIX, ORG_PREFIX)
    
    print("[DONE] Pipeline completo: duplicação, renome, join e constraints.")

# ----------------------------
# RUN
# ----------------------------
make_org_from_def_by_duplicate_join_and_constrain()
