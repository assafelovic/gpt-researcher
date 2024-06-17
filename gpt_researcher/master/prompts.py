from datetime import datetime, timezone
import warnings
from gpt_researcher.utils.enum import ReportType


def generate_search_queries_prompt(question: str, parent_query: str, report_type: str, max_iterations: int=3,):
    """ Gera as sugestões de pesquisa para a pergunta dada.
    Args: 
        question (str): A pergunta para gerar as sugestões de pesquisa prompt para
        parent_query (str): A pergunta principal (apenas relevante para relatórios detalhados)
        report_type (str): O tipo de relatório
        max_iterations (int): O número máximo de sugestões de pesquisa a serem geradas
    
    Returns: str: As sugestões de pesquisa para a pergunta fornecida
    """
    
    if report_type == ReportType.DetailedReport.value or report_type == ReportType.SubtopicReport.value:
        task = f"{parent_query} - {question}"
    else:
        task = question

    return f'Escreva {max_iterations} Consultas de pesquisa no Google para buscar online que formem uma opinião objetiva a partir da seguinte tarefa: "{task}"' \
           f'Utilize a data atual, se necessário: {datetime.now().strftime("%B %d, %Y")}.\n' \
           f'Inclua também nas consultas detalhes específicos da tarefa, como locais, nomes, etc.\n' \
           f'Você deve responder com uma lista de strings no seguinte formato: ["query 1", "query 2", "query 3"].'


def generate_report_prompt(question, context, report_format="apa", total_words=1000):
    """ Gera o prompt de relatório para a pergunta e resumo da pesquisa fornecidos.

    Args:
        question (str): A pergunta para gerar o prompt de relatório
        research_summary (str): O resumo da pesquisa para gerar o prompt de relatório

    Returns:
        str: O prompt de relatório para a pergunta e resumo da pesquisa fornecidos
    """

    return f'Informação: """{context}"""\n\n' \
           f'Usando as informações acima, responda a seguinte' \
           f' pergunta ou tarefa: "{question}" em um relatório detalhado --' \
           " O relatório deve focar na resposta à pergunta, ser bem estruturado, informativo," \
           f" em profundidade e abrangente, com fatos e números, se disponíveis, e um mínimo de {total_words} palavras.\n" \
           "Você deve se esforçar para escrever o relatório o mais longo possível usando todas as informações relevantes e necessárias fornecidas.\n" \
           "Você deve escrever o relatório com a sintaxe markdown.\n " \
           f"Use um tom imparcial e jornalístico. \n" \
           "VOCÊ DEVE determinar sua própria opinião concreta e válida com base nas informações fornecidas. NÃO faça conclusões gerais e sem sentido.\n" \
           f"VOCÊ DEVE escrever todos os URLs das fontes utilizadas no final do relatório como referências, e certifique-se de não adicionar fontes duplicadas, mas apenas uma referência para cada.\n" \
           "Cada URL deve estar hiperlinkado: [url website](url)"\
           """
            Adicionalmente, VOCÊ DEVE incluir hyperlinks para os URLs relevantes onde quer que eles sejam referenciados no relatório:
        
            eg:    
                # Report Header
                
                This is a sample text. ([url website](url))
            """\
            f"VOCÊ DEVE escrever o relatório no formato {report_format}.\n " \
            f"Cite os resultados da pesquisa usando anotações inline. Cite apenas os resultados mais \
            relevantes que respondam à pergunta com precisão. Coloque essas citações no final \
            da frase ou parágrafo que as referenciam.\n" \
            f"Por favor, faça o seu melhor, isso é muito importante para a minha carreira. " \
            f"Assuma que a data atual é {datetime.now().strftime('%B %d, %Y')}"


def generate_resource_report_prompt(question, context, report_format="apa", total_words=700):
    """Gera a sugestão de relatório de recursos para a pergunta e resumo da pesquisa fornecidos.

    Args:
        question (str): A pergunta para gerar a sugestão de relatório de recursos.
        context (str): O resumo da pesquisa para gerar a sugestão de relatório de recursos.

    Returns:
        str: A sugestão de relatório de recursos para a pergunta e resumo da pesquisa fornecidos.
    """
    return f'"""{context}"""\n\nCom base nas informações acima, gere um relatório de recomendação de bibliografia para a seguinte pergunta ou tópico: "{question}". O relatório deve fornecer uma análise detalhada de cada recurso recomendado, explicando como cada fonte pode contribuir para encontrar respostas para a pergunta de pesquisa.\n'
'Enfoque na relevância, confiabilidade e importância de cada fonte.\n'
'Certifique-se de que o relatório esteja bem estruturado, informativo, aprofundado e siga a sintaxe Markdown.\n'
'Inclua fatos, números e dados relevantes sempre que disponíveis.\n'
'O relatório deve ter um comprimento mínimo de {total_words} palavras.\n'
'VOCÊ DEVE incluir todos os URLs relevantes das fontes.'\
        'Cada URL deve estar hiperlinkado: [url website](url)'


def generate_custom_report_prompt(query_prompt, context, report_format="apa", total_words=1000):
    return f'"{context}"\n\n{query_prompt}'


def generate_outline_report_prompt(question, context, report_format="apa", total_words=1200):
    """ Gera a sugestão de esboço do relatório para a pergunta e resumo da pesquisa fornecidos..
    Args: question (str): A pergunta para gerar a sugestão de esboço do relatório
            research_summary (str): O resumo da pesquisa para gerar a sugestão de esboço do relatório
    Returns: str: A sugestão de esboço do relatório para a pergunta e resumo da pesquisa fornecidos
    """

    return f'"""{context}""" Usando as informações acima, gere um esboço para um relatório de pesquisa em sintaxe Markdown' \
           f'o seguinte questionamento ou tópico: "{question}". O esboço deve fornecer uma estrutura bem organizada' \
           ' para o relatório de pesquisa, incluindo as principais seções, subseções e pontos-chave a serem abordados.' \
           f' O relatório de pesquisa deve ser detalhado, informativo, aprofundado e ter um mínimo de {total_words} palavras.' \
           ' Usando a sintaxe Markdown apropriada para formatar o esboço e garantir a legibilidade'


def auto_agent_instructions():
    return """
        Esta tarefa envolve pesquisar um tópico específico, independentemente de sua complexidade ou da disponibilidade de uma resposta definitiva. A pesquisa é conduzida por um servidor específico, definido por seu tipo e função, sendo que cada servidor requer instruções distintas.
        Agent
        O servidor é determinado pelo campo do tópico e pelo nome específico do servidor que pode ser utilizado para pesquisar o tópico fornecido. Os agentes são categorizados por sua área de especialização, e cada tipo de servidor está associado a um emoji correspondente.

        examples:
        task: "Devo investir em ações da Apple?"
        response: 
        {
            "server": "💰 Agente Financeiro",
            "agent_role_prompt: "Você é um assistente de inteligência artificial experiente em análise financeira. Seu objetivo principal é compor relatórios financeiros abrangentes, perspicazes, imparciais e metodicamente organizados com base nos dados e tendências fornecidos."
        }
        task: "A revenda de tênis pode se tornar lucrativa?"
        response: 
        { 
            "server":  "📈 Agente de Análise de Negócios",
            "agent_role_prompt": "Você é um assistente de inteligência artificial experiente em análise de negócios. Seu principal objetivo é produzir relatórios empresariais abrangentes, perspicazes, imparciais e estruturados de forma sistemática com base nos dados empresariais fornecidos, nas tendências de mercado e na análise estratégica."
        }
        task: "Quais são os locais mais interessantes em Tel Aviv?"
        response:
        {
            "server:  "🌍 Agente de Viagens",
            "agent_role_prompt": "Você é um assistente de inteligência artificial experiente em viagens pelo mundo. Seu principal objetivo é elaborar relatórios de viagem envolventes, esclarecedores, imparciais e bem estruturados sobre locais específicos, incluindo história, atrações e informações culturais."
        }
    """


def generate_summary_prompt(query, data):
    """ Gera o prompt de resumo para a pergunta e texto fornecidos.
    Args: question (str): A pergunta para gerar o prompt de resumo para
            text (str): O texto para gerar o prompt de resumo para
    Returns: str: O prompt de resumo para a pergunta e texto fornecidos
    """

    return f'{data}\n Usando o texto acima, resuma-o com base na seguinte tarefa ou consulta: "{query}". Se a ' \
           f'consulta não puder ser respondida usando o texto, VOCÊ DEVE resumir o texto de\n forma resumida. Inclua todas as informações factuais, ' \
           f'como números, estatísticas, citações, etc., se disponíveis. '


################################################################################################

# DETAILED REPORT PROMPTS

def generate_subtopics_prompt() -> str:
    return """
                Fornecido o tópico principal:
                
                {task}
                
                e dados de pesquisa:
                
                {data}
                
                - Construa uma lista de subtemas que indiquem os títulos de um documento de relatório a ser gerado sobre a tarefa.
                - Esta é uma lista possível de subtemas: {subtopics}.
                - Não deve haver subtemas duplicados.
                - Limite o número de subtemas a um máximo de {max_subtopics}.
                - Por fim, ordene os subtemas de acordo com suas tarefas, em uma ordem relevante e significativa que seja apresentável em um relatório detalhado.
                
                "IMPORTANT!":
                - Cada subtema DEVE ser relevante para o tópico principal e aos dados de pesquisa fornecidos SOMENTE!
                
                {format_instructions}
            """


def generate_subtopic_report_prompt(
    current_subtopic,
    existing_headers,
    main_topic,
    context,
    report_format="apa",
    total_words=1000,
    max_subsections=5,
) -> str:

    return f"""
    "Context":
    "{context}"
    
    "Tópico Principal e Subtópico":
    Com base nas informações mais recentes disponíveis, elabore um relatório detalhado sobre o subtópico: {current_subtopic} dentro do tópico principal: {main_topic}.
Você deve limitar o número de subseções a um máximo de {max_subsections}.
    
    "Foco do Conteúdo":
    - O relatório deve focar em responder à pergunta, ser bem estruturado, informativo, aprofundado e incluir fatos e números, se disponíveis.
    - Utilize a sintaxe Markdown e siga o formato {report_format.upper()}.
    
    "Estrutura e Formatação":
- Como este sub-relatório fará parte de um relatório maior, inclua apenas o corpo principal dividido em subtópicos adequados, sem qualquer seção de introdução ou conclusão.
    
    - VOCÊ DEVE incluir hiperlinks em markdown para URLs de fontes relevantes sempre que referenciadas no relatório, por exemplo:
    
        # Cabeçalho do Relatório
        
        Este é um texto de exemplo. ([url website](url))
    
    "Relatórios de Subtópicos Existentes":
        - Esta é uma lista de relatórios de subtópicos existentes e seus cabeçalhos de seção:
    
        {existing_headers}.
    
    - Não utilize nenhum dos cabeçalhos acima ou detalhes relacionados para evitar duplicações. Use cabeçalhos menores em Markdown (por exemplo, H2 ou H3) para a estrutura do conteúdo, evitando o maior cabeçalho (H1), pois ele será usado para o título do relatório maior.
    
    "Date":
    Assuma que a data atual é {datetime.now(timezone.utc).strftime('%d de %B de %Y')} se necessário.
    
    "IMPORTANT!":
    - O foco DEVE estar no tópico principal! Você DEVE deixar de fora qualquer informação que não esteja relacionada a ele!
    - NÃO deve haver introdução, conclusão, resumo ou seção de referências.
    - Você DEVE incluir hyperlinks com a sintaxe markdown ([url website](url)) relacionados às frases sempre que necessário.
    - O relatório deve ter um comprimento mínimo de {total_words} palavras.
    """


def generate_report_introduction(question: str, research_summary: str = "") -> str:
    return f"""{research_summary}\n 
        Usando as informações mais recentes acima, prepare uma introdução detalhada do relatório sobre o tópico -- {question}.
        - A introdução deve ser sucinta, bem estruturada e informativa, com sintaxe markdown.
        - Como esta introdução fará parte de um relatório maior, NÃO inclua outras seções, que geralmente estão presentes em um relatório.
        - A introdução deve ser precedida por um título H1 com um tópico adequado para o relatório completo.
        - Você deve incluir hyperlinks com sintaxe markdown ([url website](url)) relacionados às frases sempre que necessário.
        - Assuma que a data atual é {datetime.now(timezone.utc).strftime('%d de %B de %Y')} se necessário.
    """


report_type_mapping = {
    ReportType.ResearchReport.value: generate_report_prompt,
    ReportType.ResourceReport.value: generate_resource_report_prompt,
    ReportType.OutlineReport.value: generate_outline_report_prompt,
    ReportType.CustomReport.value: generate_custom_report_prompt,
    ReportType.SubtopicReport.value: generate_subtopic_report_prompt
}


def get_prompt_by_report_type(report_type):
    prompt_by_type = report_type_mapping.get(report_type)
    default_report_type = ReportType.ResearchReport.value
    if not prompt_by_type:
        warnings.warn(f"Tipo de relatório inválido: {report_type}.\n"
                        f"Por favor, use um dos seguintes: {', '.join([enum_value for enum_value in report_type_mapping.keys()])}\n"
                        f"Usando tipo de relatório padrão: {default_report_type} prompt.",
                        UserWarning)
        prompt_by_type = report_type_mapping.get(default_report_type)
    return prompt_by_type
