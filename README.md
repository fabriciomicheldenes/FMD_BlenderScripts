# Blender Utility Scripts

Coleção de scripts em Python desenvolvidos para automatizar tarefas no **Blender**, com foco em **Rigging**, **Manipulação de Armatures** e **Workflow Técnico**.  
Este repositório serve como um conjunto de ferramentas úteis para agilizar produção de rigs, animações técnicas e setups de personagens ou máquinas.

---

## ✨ Funcionalidades Principais

### ✔ Orientação Automática de Bones (Parent → Child)
Script que:
- Usa o **bone ativo** como *pai*  
- Usa todos os **bones selecionados** como *filhos*  
- Reposiciona cada filho no **tail** do pai  
- Alinha o **eixo Y do filho** exatamente ao **eixo X local do pai**  
- Ajusta o *roll* com base no **eixo Z** do pai  
- Mantém perpendicularidade perfeita entre pai e filho  
- Funciona em **Edit Mode**

É ideal para rigs mecânicos, setups de tentáculos, membros artificiais e estruturas hierárquicas precisas.

---

## 📌 Exemplo de uso (Edit Mode)

1. Selecione um ou vários bones filhos.  
2. Selecione o bone pai **por último** (ele se torna o *ativo*).  
3. Execute o script

