import os
import pandas as pd
from tqdm.auto import tqdm
from itertools import product
from multiprocessing import Pool


def run_sim(arquivo, config_il1_: str, alg_il1_: str, config_dl1_: str, alg_dl1_: str, key1_: int, key2_: int):
    """
    Executa o comando da simulação.
    :param arquivo: Caminho com o arquivo a ser executado.
    :param config_il1_: Parametros de 'il1'.
    :param alg_il1_: Código do algoritmo de substituicao do 'il1'.
    :param config_dl1_: Paramentros de 'dl1'.
    :param alg_dl1_: Código do algoritmo de substituicao do 'dl1'.
    :param key1_: Index do parametro usado para 'il1'.
    :param key2_: Index do parametro usado para 'dl1'.
    """
    os.system(f"./sim-cache -cache:il1 i{config_il1_}{alg_il1_} -cache:il2 none "
              f"-cache:dl1 d{config_dl1_}{alg_dl1_} -cache:dl2 none -redir:sim "
              f"Resultados_otimizados/{str(key1_) + '_' + alg_il1_ + '_' + str(key2_) + '_' + alg_dl1_}.txt "
              f"{arquivo}")


def combinacao_parametros(tamanho_memoria: int) -> list:
    """
    Gera uma lista com combinação de todos parametros para a execução do simulador.
    :param tamanho_memoria: Tamanho de memória desejado para ser testado.
    :return: Lista com os parametros.
    """
    for param in product([1, 2, 4, 8, 16, 32, 64, 128, 256], repeat=3):
        # Tem que ser maior igual a outro pois o simulador não aceita
        if param[0] * param[1] * param[2] == tamanho_memoria and param[1] >= 8:
            yield param


def todas_combinacoes(arquivo: str, testes_possiveis: list, algoritmo_de_substituicao=None, pular=0, n_processos=1):
    """
    Gera os arquivos de output para todos as combinaçoes de testes possíveis com todos algoritmos de substituicao.
    :param arquivo: Nome do arquivo pra rodar na simulacao.
    :param testes_possiveis: Lista com todos testes a serem realizados.
    :param algoritmo_de_substituicao: Algoritmos de substituicao desejados, por padrão ele usa ['l', 'f'].
    :param pular: Caso seja desejado pular algum numero de testes.
    :param n_processos: Numero de simulacoes sendo rodadas em paralelo.
    """
    algoritmo_de_substituicao = algoritmo_de_substituicao if algoritmo_de_substituicao is not None else ['l', 'f']
    contador = 0
    with Pool(processes=n_processos) as pool:
        for alg_il1 in tqdm(algoritmo_de_substituicao):
            for key1, config_il1 in enumerate(testes_possiveis):
                for alg_dl1 in algoritmo_de_substituicao:
                    for key2, config_dl1 in enumerate(testes_possiveis):
                        contador += 1
                        if contador > pular:
                            pool.apply_async(run_sim, args=(arquivo, config_il1, alg_il1,
                                                            config_dl1, alg_dl1, key1, key2))
        pool.close()
        pool.join()


def testes_otimizados(arquivo: str, testes_possiveis: list, algoritmo_de_substituicao=None, n_processos=1,
                      force_cod_il1='l1:1:256:1:', force_alg_il1='l', force_cod_dl1='l1:1:32:8:', force_alg_dl1='l'):
    """
    Gera os arquivos de output para todos as combinaçoes de testes possíveis com todos algoritmos de substituicao.
    :param arquivo: Nome do arquivo pra rodar na simulacao.
    :param testes_possiveis: Lista com todos testes a serem realizados.
    :param algoritmo_de_substituicao: Algoritmos de substituicao desejados, por padrão ele usa ['l', 'f'].
    :param force_cod_il1: Force parametro de 'il1'.
    :param force_alg_il1: Force código do algoritmo de substituicao do 'il1'.
    :param force_cod_dl1: Force parametro de 'dl1'.
    :param force_alg_dl1: Force código do algoritmo de substituicao do 'dl1'.
    :param n_processos: Numero de simulacoes sendo rodadas em paralelo.
    """
    algoritmo_de_substituicao = algoritmo_de_substituicao if algoritmo_de_substituicao is not None else ['l', 'f']
    with Pool(processes=n_processos) as pool:
        for alg_il1 in tqdm(algoritmo_de_substituicao):
            for key1, config_il1 in enumerate(testes_possiveis):
                pool.apply_async(run_sim, args=(arquivo, config_il1, alg_il1, force_cod_dl1, force_alg_dl1, key1, 2))
        pool.close()
        pool.join()

    with Pool(processes=n_processos) as pool:
        for alg_dl1 in tqdm(algoritmo_de_substituicao):
            for key2, config_dl1 in enumerate(testes_possiveis):
                pool.apply_async(run_sim, args=(arquivo, force_cod_il1, force_alg_il1, config_dl1, alg_dl1, 5, key2))
        pool.close()
        pool.join()


def criador_codigos(tamanho_memoria: int) -> list:
    """
    Geram os códigos ja prontos para serem passados como argumentos.
    :param tamanho_memoria: Tamanho desejado da memoria.
    :return: Lista com os códigos ja montados.
    """
    lista_de_codigos = []
    for parametro in combinacao_parametros(tamanho_memoria):
        lista_de_codigos.append(f"l1:{parametro[0]}:{parametro[1]}:{parametro[2]}:")
    return lista_de_codigos


def junta_resultados_excel(diretorio: str, arquivo_output: str, lista_testes: list, linha_inicial: int,
                           linha_final: int):
    """
    Abre os arquivos e usa o pandas para juntar todos os resultados em uma planilha do excel.
    :param diretorio: Nome do diretorio com os arquivos de output do simulador.
    :param arquivo_output: Nome do arquivo de output do excel.
    :param lista_testes: Lista com os codigos de teste para buscar pelo index.
    :param linha_inicial: Index da linha inicial dos resultados das simulacoes (Começa em 0, então tira 1 pra começar
        na linha certa).
    :param linha_final: Index da linha final dos resultados das simulacoes.
    """
    df = pd.DataFrame()
    descricoes = []
    pega_descricao = True
    for arquivo in tqdm(os.listdir(diretorio)):
        if arquivo.endswith('.txt'):
            with open(os.path.join(diretorio, arquivo), 'r') as arquivo_texto:
                linhas = arquivo_texto.readlines()[linha_inicial:linha_final]
                resultados = []
                for linha in linhas:
                    conteudo = linha.split()
                    if pega_descricao:
                        descricoes.append(conteudo[0])
                    resultados.append(conteudo[1])
                pega_descricao = False
                val = arquivo[:-4].split("_")
                identificadores = str(lista_testes[int(val[0])]).split(':')[1:-1] + [val[1]]
                identificadores = identificadores + str(lista_testes[int(val[2])]).split(':')[1:-1] + [val[3]]
                nova_coluna_df = pd.DataFrame(identificadores + resultados)
                df = pd.concat([df, nova_coluna_df], axis=1)
    df = df.T
    descricoes = ['il1<nsets>', 'il1<bsize>', 'il1<assoc>', 'il1<repl>',
                  'dl1<nsets>', 'dl1<bsize>', 'dl1<assoc>', 'dl1<repl>'] + descricoes
    df.columns = descricoes
    df.to_excel(arquivo_output, index=False)


def main(tamanho_memoria, arquivo, tipo_teste, n_processos, caminho_resultados, arquivo_final, index_inicio, index_fim):
    if tamanho_memoria < 8:
        raise Exception('Tamanho minimo da memoria tem que ser maior que 8 pois o simulador não aceita tamanho menor '
                        'que 8 para o blocksize.')
    if n_processos < 1:
        raise Exception('Poxa... nao da pra rodar nenhuma ou threads negativas.')

    testes = criador_codigos(tamanho_memoria)

    match tipo_teste:
        case 'todos':
            todas_combinacoes(arquivo, testes, n_processos=n_processos)
        case 'otimizado':
            testes_otimizados(arquivo, testes, n_processos=n_processos)
        case 'pular':
            pass
        case _:
            raise Exception('Era esperado um dos seguintes valores em "tipo_de_teste": "todos", "otimizado", "pular".')

    junta_resultados_excel(caminho_resultados, arquivo_final, testes, index_inicio, index_fim)


if __name__ == '__main__':
    main(arquivo='./bench_trabalho/basicmath.ss', tamanho_memoria=256, n_processos=5, tipo_teste='pular',
         caminho_resultados='/home/ferna/Arquitetura/SimpleScalar/Resultados_otimizados',
         arquivo_final='basicmath2_output.xlsx', index_inicio=70, index_fim=128)
