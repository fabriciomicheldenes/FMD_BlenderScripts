import bpy
import mathutils

def orient_child_using_selection(length=1.0):
    """
    Usa o bone ATIVO como pai e todos os selecionados (exceto o ativo) como filhos.
    Funciona somente em Edit Mode.
    """

    arm = bpy.context.object
    eb = arm.data.edit_bones

    # Bone pai = ativo
    parent = eb.active

    if parent is None:
        raise RuntimeError("Nenhum bone ativo encontrado. Selecione um PAI!")

    # Filhos = selecionados - ativo
    selected_bones = [b for b in eb if b.select and b != parent]

    if not selected_bones:
        raise RuntimeError("Selecione pelo menos um bone FILHO além do ativo!")

    # Matriz do pai
    M = parent.matrix.copy()

    # Eixos locais do pai
    x_local_parent = M.col[0].to_3d().normalized()
    z_local_parent = M.col[2].to_3d().normalized()

    for child in selected_bones:

        # 1) HEAD DO FILHO = TAIL DO PAI
        child.head = parent.tail.copy()

        # 2) Direção do filho = eixo X do pai
        child.tail = child.head + x_local_parent * length

        # 3) Ajeita o ROLL para que o eixo X do filho
        #    esteja alinhado com o eixo Z do pai
        child.align_roll(z_local_parent)

        print(f"[OK] Filhos '{child.name}' orientado a 90° do pai '{parent.name}'.")

    print("Todos os bones filhos foram orientados com sucesso!")


# ===================================
# EXEMPLO (basta rodar assim):
# ===================================
orient_child_using_selection(length=1.5)
