import json
import os
from difflib import SequenceMatcher

base_path = r"C:\Users\dario\kenlo_files"

files = {
    "apropriacoes": os.path.join(base_path, "apropriacoes.json"),
    "contratos": os.path.join(base_path, "contratos_oficial.json"),
    "repasse1": os.path.join(base_path, "repasse_join1.json"),
    "repasse2": os.path.join(base_path, "repasse_join2.json"),
    "apropriacoes_descontos": os.path.join(base_path, "apropriacoes_descontos.json"),
    "imoveis": os.path.join(base_path, "imoveis_organizados.json"),
}

def load_json(file_path):
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar o arquivo {file_path}: {e}")
        return []

def buscar_contrato_por_imovel(contratos, id_imovel):
    for contrato in contratos:
        if contrato.get("id_imovel_imo") == str(id_imovel):
            return contrato
    return None

def buscar_apropriacoes_por_imovel(apropriacoes, id_imovel):
    return [item for item in apropriacoes if str(item.get("id_imovel_imo")) == str(id_imovel)]

def buscar_dados_repasse(repasses, id_favorecido=None, id_imovel=None):
    valor_segmentado = None
    historico_segmentado = None
    nome_segmentado = None
    valor_agrupado = 0
    nome_agrupado = None
    historico_agrupado = None
    encontrou_agrupado = False

    # 1. Busca valor segmentado por imóvel+favorecido
    if id_favorecido and id_imovel:
        for repasse in repasses:
            if (
                str(repasse.get("id_favorecido_fav")) == str(id_favorecido)
                and str(repasse.get("id_imovel_imo")) == str(id_imovel)
            ):
                nome_segmentado = repasse.get("st_nome_fav")
                valor_segmentado = repasse.get("vl_valor_mov")
                historico_segmentado = repasse.get("st_historico_mov")
                break

    # 2. Valor agrupado (total para o favorecido)
    if id_favorecido:
        for repasse in repasses:
            if str(repasse.get("id_favorecido_fav")) == str(id_favorecido):
                encontrou_agrupado = True
                try:
                    valor_agrupado += float(repasse.get("vl_valor_mov", 0))
                except Exception:
                    pass
                if not nome_agrupado:
                    nome_agrupado = repasse.get("st_nome_fav")
                    historico_agrupado = repasse.get("st_historico_mov")

    return {
        "st_nome_fav": nome_segmentado or nome_agrupado,
        "valor_repasse": valor_segmentado,
        "st_historico_mov": historico_segmentado,
        "valor_repasse_agrupado": valor_agrupado if encontrou_agrupado else None,
        "st_historico_mov_agrupado": historico_agrupado,
        "st_nome_fav_agrupado": nome_agrupado,
    }

def buscar_descontos(descontos, id_imovel, id_favorecido):
    for desconto in descontos:
        if desconto.get("id_imovel_imo") == str(id_imovel) and desconto.get("id_favorecido_fav") == str(id_favorecido):
            return {
                "valor_apropriacao_desconto_descricao": desconto.get("st_descricao_cont"),
                "valor_apropriacao_desconto_valor": desconto.get("valor")
            }
    return {
        "valor_apropriacao_desconto_descricao": None,
        "valor_apropriacao_desconto_valor": None
    }

def formatar_valor(valor):
    if valor is None:
        return None
    try:
        return f"{float(valor):.2f}"
    except Exception:
        return None

def buscar_nomes_proprietarios(imovel):
    if not imovel:
        return None
    proprietarios = imovel.get("proprietarios_beneficiarios")
    if proprietarios and isinstance(proprietarios, list):
        nomes = [p.get("st_nome_pes") for p in proprietarios if p.get("st_nome_pes")]
        return ", ".join(nomes) if nomes else None
    return None

def buscar_imovel_por_id(imoveis, id_imovel):
    lista = imoveis.get("data") if isinstance(imoveis, dict) and "data" in imoveis else imoveis
    for imovel in lista:
        if str(imovel.get("id_imovel_imo")) == str(id_imovel):
            return imovel
    return None

def get_all_id_imovel(*json_lists):
    ids = set()
    for lista in json_lists:
        if isinstance(lista, dict) and "data" in lista:
            items = lista["data"]
        else:
            items = lista
        if isinstance(items, list):
            for item in items:
                id_imovel = item.get("id_imovel_imo")
                if id_imovel is not None:
                    ids.add(str(id_imovel))
    return ids

def similar(a, b):
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def match_endereco(imo, item):
    if not imo:
        return False
    campos_imo = [imo.get("st_endereco_imo", ""), imo.get("st_numero_imo", ""), imo.get("st_bairro_imo", "")]
    endereco_imo = " ".join(str(s) for s in campos_imo if s)
    enderecos_possiveis = [
        item.get("st_endereco_imo", ""),
        item.get("st_complemento_mov", ""),
        item.get("st_bairro_imo", ""),
        item.get("st_numero_imo", ""),
        item.get("st_endereco", ""),
    ]
    for endereco in enderecos_possiveis:
        if endereco and similar(endereco_imo, str(endereco)) > 0.85:
            return True
    return False

def match_valor_aluguel(imo, item):
    if not imo:
        return False
    valor_imo = imo.get("vl_aluguel_imo")
    campos_possiveis = [
        item.get("vl_aluguel_con"),
        item.get("vl_valor_mov"),
        item.get("valor"),
        item.get("vl_original_mova"),
    ]
    try:
        valor_imo = float(valor_imo)
        for v in campos_possiveis:
            try:
                if v is not None and abs(float(v) - valor_imo) < 1e-2:
                    return True
            except:
                continue
    except:
        pass
    return False

def buscar_match_extra_por_nome_endereco_valor(imo, outros_jsons):
    if not imo:
        return None, None, None
    nomes_proprietarios = []
    proprietarios = imo.get("proprietarios_beneficiarios")
    if proprietarios and isinstance(proprietarios, list):
        nomes_proprietarios = [p.get("st_nome_pes") for p in proprietarios if p.get("st_nome_pes")]

    endereco_imo = " ".join(str(imo.get(campo, "")) for campo in ["st_endereco_imo", "st_numero_imo", "st_bairro_imo"] if imo.get(campo))
    valor_imo = imo.get("vl_aluguel_imo")

    match_nome = None
    match_end = None
    match_valor = None

    for nome_json, lista in outros_jsons:
        if isinstance(lista, dict) and "data" in lista:
            items = lista["data"]
        else:
            items = lista
        for item in items:
            # MATCH por nome proprietário
            if not match_nome:
                for nome_prop in nomes_proprietarios:
                    for campo_nome in ["st_nome_fav", "st_favorecido"]:
                        if campo_nome in item and item[campo_nome]:
                            if similar(nome_prop, item[campo_nome]) > 0.85:
                                match_nome = item[campo_nome]
                                break
                    if match_nome:
                        break
            # MATCH por endereço
            if not match_end and match_endereco(imo, item):
                _enderecos = [item.get(campo) for campo in ["st_endereco_imo", "st_numero_imo", "st_bairro_imo", "st_endereco", "st_complemento_mov"] if item.get(campo)]
                match_end = ", ".join(_enderecos)
            # MATCH por valor aluguel
            if not match_valor and match_valor_aluguel(imo, item):
                for campo in ["vl_aluguel_con", "vl_valor_mov", "valor", "vl_original_mova"]:
                    if item.get(campo) is not None:
                        match_valor = item.get(campo)
                        break
            if match_nome and match_end and match_valor:
                break
        if match_nome and match_end and match_valor:
            break
    return match_nome, match_end, match_valor

def buscar_endereco_por_id(id_imovel, imoveis, apropriacoes, contratos, repasse1, repasse2, descontos):
    # 1. Imóveis
    imovel = buscar_imovel_por_id(imoveis, id_imovel)
    if imovel:
        for campo in ["st_endereco_imo", "st_endereco"]:
            if imovel.get(campo):
                return {
                    "st_endereco_imo": imovel.get("st_endereco_imo") or imovel.get("st_endereco"),
                    "st_numero_imo": imovel.get("st_numero_imo"),
                    "st_bairro_imo": imovel.get("st_bairro_imo")
                }
    # 2. Apropriações
    for item in apropriacoes:
        if str(item.get("id_imovel_imo")) == str(id_imovel):
            for campo in ["st_endereco_imo", "st_endereco"]:
                if item.get(campo):
                    return {
                        "st_endereco_imo": item.get("st_endereco_imo") or item.get("st_endereco"),
                        "st_numero_imo": item.get("st_numero_imo"),
                        "st_bairro_imo": item.get("st_bairro_imo")
                    }
    # 3. Contratos
    for item in contratos:
        if str(item.get("id_imovel_imo")) == str(id_imovel):
            for campo in ["st_endereco_imo", "st_endereco"]:
                if item.get(campo):
                    return {
                        "st_endereco_imo": item.get("st_endereco_imo") or item.get("st_endereco"),
                        "st_numero_imo": item.get("st_numero_imo"),
                        "st_bairro_imo": item.get("st_bairro_imo")
                    }
    # 4. Repasses 1
    for item in repasse1:
        if str(item.get("id_imovel_imo")) == str(id_imovel):
            for campo in ["st_endereco_imo", "st_endereco"]:
                if item.get(campo):
                    return {
                        "st_endereco_imo": item.get("st_endereco_imo") or item.get("st_endereco"),
                        "st_numero_imo": item.get("st_numero_imo"),
                        "st_bairro_imo": item.get("st_bairro_imo")
                    }
    # 5. Repasses 2
    lista = repasse2.get("data", []) if isinstance(repasse2, dict) else repasse2
    for item in lista:
        if str(item.get("id_imovel_imo")) == str(id_imovel):
            for campo in ["st_endereco_imo", "st_endereco"]:
                if item.get(campo):
                    return {
                        "st_endereco_imo": item.get("st_endereco_imo") or item.get("st_endereco"),
                        "st_numero_imo": item.get("st_numero_imo"),
                        "st_bairro_imo": item.get("st_bairro_imo")
                    }
    # 6. Descontos
    for item in descontos:
        if str(item.get("id_imovel_imo")) == str(id_imovel):
            for campo in ["st_endereco_imo", "st_endereco"]:
                if item.get(campo):
                    return {
                        "st_endereco_imo": item.get("st_endereco_imo") or item.get("st_endereco"),
                        "st_numero_imo": item.get("st_numero_imo"),
                        "st_bairro_imo": item.get("st_bairro_imo")
                    }
    return {
        "st_endereco_imo": None,
        "st_numero_imo": None,
        "st_bairro_imo": None
    }

def buscar_valor_aluguel_contrato_fallback(contratos, nome_inquilino, endereco, codigo_contrato):
    for contrato in contratos:
        # Elo: código contrato
        if codigo_contrato and str(contrato.get("id_contrato_con")) == str(codigo_contrato):
            valor = contrato.get("vl_aluguel_con")
            if valor:
                try:
                    return f"{float(valor):.2f}"
                except Exception:
                    return valor
        # Elo: nome do inquilino
        if nome_inquilino and contrato.get("inquilinos"):
            for inq in contrato.get("inquilinos"):
                if inq.get("st_fantasia_pes") and inq.get("st_fantasia_pes") == nome_inquilino:
                    valor = contrato.get("vl_aluguel_con")
                    if valor:
                        try:
                            return f"{float(valor):.2f}"
                        except Exception:
                            return valor
        # Elo: endereço
        for campo in ["st_endereco_imo", "st_endereco"]:
            if endereco and contrato.get(campo) and contrato.get(campo) == endereco:
                valor = contrato.get("vl_aluguel_con")
                if valor:
                    try:
                        return f"{float(valor):.2f}"
                    except Exception:
                        return valor
    return None

def process_data(imoveis, apropriacoes, contratos, repasse1, repasse2, descontos):
    result = []
    todos_repasses = (repasse1 if isinstance(repasse1, list) else []) + (repasse2.get("data", []) if isinstance(repasse2, dict) else [])
    lista_imoveis = imoveis.get("data") if isinstance(imoveis, dict) and "data" in imoveis else imoveis

    all_ids_imovel = get_all_id_imovel(
        lista_imoveis, apropriacoes, contratos, repasse1, repasse2, descontos
    )

    outros_jsons = [
        ("apropriacoes", apropriacoes),
        ("contratos", contratos),
        ("repasse1", repasse1),
        ("repasse2", repasse2),
        ("apropriacoes_descontos", descontos)
    ]

    for id_imovel in all_ids_imovel:
        imovel = buscar_imovel_por_id(imoveis, id_imovel)
        contrato = buscar_contrato_por_imovel(contratos, id_imovel)
        endereco = buscar_endereco_por_id(
            id_imovel,
            imoveis,
            apropriacoes,
            contratos,
            repasse1,
            repasse2,
            descontos
        )
        aprop_do_imovel = buscar_apropriacoes_por_imovel(apropriacoes, id_imovel)
        nome_inquilino = contrato.get("inquilinos")[0].get("st_fantasia_pes") if contrato and contrato.get("inquilinos") else None
        codigo_contrato = contrato.get("id_contrato_con") if contrato else None
        endereco_imo = endereco["st_endereco_imo"]
        if aprop_do_imovel:
            for item in aprop_do_imovel:
                id_favorecido = item.get("id_favorecido_fav")
                repasse = buscar_dados_repasse(todos_repasses, id_favorecido=id_favorecido, id_imovel=id_imovel)
                desconto = buscar_descontos(descontos, id_imovel, id_favorecido)
                st_nome_fav = repasse["st_nome_fav"] if repasse["st_nome_fav"] else buscar_nomes_proprietarios(imovel)
                if not st_nome_fav:
                    match_nome, match_end, match_valor = buscar_match_extra_por_nome_endereco_valor(imovel, outros_jsons)
                    if match_nome:
                        st_nome_fav = match_nome
                valor_aluguel = formatar_valor(imovel.get("vl_aluguel_imo")) if imovel else None
                if not valor_aluguel:
                    valor_aluguel = buscar_valor_aluguel_contrato_fallback(contratos, nome_inquilino, endereco_imo, codigo_contrato)
                if not valor_aluguel:
                    _, _, match_valor = buscar_match_extra_por_nome_endereco_valor(imovel, outros_jsons)
                    if match_valor:
                        valor_aluguel = formatar_valor(match_valor)
                formatted_data = {
                    "id_imovel": str(id_imovel),
                    "id_favorecido": str(id_favorecido) if id_favorecido else None,
                    "origem": "movimentacao",
                    "valor_movimentacao": formatar_valor(item.get("valor", 0)),
                    "descricao_pagamento": item.get("st_complemento_mov"),
                    "st_descricao_cont": item.get("st_descricao_cont"),
                    "valor_apropriacao": formatar_valor(item.get("vl_original_mova")),
                    "valor_apropriacao_desconto_descricao": desconto["valor_apropriacao_desconto_descricao"],
                    "valor_apropriacao_desconto_valor": formatar_valor(desconto["valor_apropriacao_desconto_valor"]),
                    "valor_repasse": formatar_valor(repasse["valor_repasse"]),
                    "valor_repasse_agrupado": formatar_valor(repasse["valor_repasse_agrupado"]),
                    "st_nome_fav": st_nome_fav,
                    "st_historico_mov": repasse["st_historico_mov"],
                    "nome_inquilino": nome_inquilino,
                    "valor_aluguel": valor_aluguel,
                    "tx_adm": formatar_valor(contrato.get("tx_adm_con")) if contrato else None,
                    "st_endereco_imo": endereco["st_endereco_imo"],
                    "st_numero_imo": endereco["st_numero_imo"],
                    "st_bairro_imo": endereco["st_bairro_imo"],
                    "st_nome_filial": imovel.get("st_nome_fil") if imovel else None,
                    "codigo_contrato": codigo_contrato
                }
                result.append(formatted_data)
        else:
            st_nome_fav = buscar_nomes_proprietarios(imovel)
            valor_aluguel = formatar_valor(imovel.get("vl_aluguel_imo")) if imovel else None
            if not valor_aluguel:
                valor_aluguel = buscar_valor_aluguel_contrato_fallback(contratos, nome_inquilino, endereco_imo, codigo_contrato)
            match_nome, match_end, match_valor = buscar_match_extra_por_nome_endereco_valor(imovel, outros_jsons)
            if not st_nome_fav:
                st_nome_fav = match_nome
            if not valor_aluguel and match_valor:
                valor_aluguel = formatar_valor(match_valor)
            formatted_data = {
                "id_imovel": str(id_imovel),
                "id_favorecido": None,
                "origem": None,
                "valor_movimentacao": None,
                "descricao_pagamento": None,
                "st_descricao_cont": None,
                "valor_apropriacao": None,
                "valor_apropriacao_desconto_descricao": None,
                "valor_apropriacao_desconto_valor": None,
                "valor_repasse": None,
                "valor_repasse_agrupado": None,
                "st_nome_fav": st_nome_fav,
                "st_historico_mov": None,
                "nome_inquilino": nome_inquilino,
                "valor_aluguel": valor_aluguel,
                "tx_adm": formatar_valor(contrato.get("tx_adm_con")) if contrato else None,
                "st_endereco_imo": endereco["st_endereco_imo"],
                "st_numero_imo": endereco["st_numero_imo"],
                "st_bairro_imo": endereco["st_bairro_imo"],
                "st_nome_filial": imovel.get("st_nome_fil") if imovel else None,
                "codigo_contrato": codigo_contrato
            }
            result.append(formatted_data)
    return result

if __name__ == "__main__":
    data_arquivo = {key: load_json(path) for key, path in files.items()}

    processed_data = process_data(
        data_arquivo["imoveis"],
        data_arquivo["apropriacoes"],
        data_arquivo["contratos"],
        data_arquivo["repasse1"],
        data_arquivo["repasse2"],
        data_arquivo["apropriacoes_descontos"]
    )

    output_file = os.path.join(base_path, "imoveis_tratados_resultado2.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=4)

    print(f"Dados processados e salvos em {output_file}")