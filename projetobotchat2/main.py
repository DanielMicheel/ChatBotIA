# main.py

from google import genai
from google.genai import types
import config
import database
import re

def get_menu_option(choice_input):
    """
    Interpreta a escolha do menu de forma flexível:
    - Retorna 1 se a entrada corresponder à opção de alugar carro.
    - Retorna 2 se a entrada corresponder à opção de dúvidas sobre a empresa.
    - Retorna 3 se a entrada corresponder à opção de sair.
    - Retorna 0 se não reconhecer a opção.
    """
    choice = choice_input.lower().strip()
    if choice == "1" or "alugar" in choice:
        return 1
    elif choice == "2" or "empresa" in choice or "dúvida" in choice:
        return 2
    elif choice == "3" or "sair" in choice or "exit" in choice or "quit" in choice:
        return 3
    else:
        return 0

def generate_filter_question(client, conversation_history=""):
    """
    Usa a IA para gerar uma pergunta de filtro relevante para identificar a melhor opção
    de carro, com base nas informações gerais sobre nossa frota.
    
    Nossa frota (dados simulados): 
      - Capacidade: 4 a 5 passageiros
      - Diária: de R$80 a R$150
      - Tipos: Sedan, Hatch e SUV
      
    O prompt instrui a IA a fazer uma única pergunta objetiva, sem perguntar nada irrelevante.
    """
    prompt = (
        "Você é um assistente especializado em aluguel de carros e precisa filtrar a melhor opção para o cliente. "
        "Nossos veículos disponíveis costumam ter as seguintes características: "
        "capacidade entre 4 e 5 passageiros, diária entre R$80 a R$150 e os tipos são Sedan, Hatch e SUV. "
        "Baseando-se nessas informações, faça apenas uma pergunta objetiva que ajude a identificar a necessidade do cliente. "
        "A pergunta deve estar relacionada a um dos seguintes critérios: número de passageiros, orçamento máximo ou preferência por tipo de carro. "
    )
    if conversation_history:
        prompt += f"Histórico anterior de interação:\n{conversation_history}\n"
    prompt += "Forneça somente a pergunta."

    response = client.models.generate_content(
        model=config.MODEL_ID,
        contents=[prompt],
        config=types.GenerateContentConfig(max_output_tokens=100, temperature=0.2)
    )
    question_text = response.text.strip()
    return question_text

def extract_filter_data(answers):
    """
    A partir das respostas coletadas, tenta extrair:
      - Número mínimo de passageiros (busca o primeiro número inteiro)
      - Valor do orçamento (procura número com ou sem decimal)
      - Preferência de tipo de carro (texto livre, se detectado)
      
    Caso algum dado não seja extraído, são definidos valores padrão.
    """
    num_passengers = None
    budget = None
    car_type_preference = None

    for question, answer in answers.items():
        lower_q = question.lower()
        if "passageiro" in lower_q:
            match = re.search(r'\d+', answer)
            if match:
                num_passengers = int(match.group())
        if ("diária" in lower_q or "orçamento" in lower_q or "preço" in lower_q or "valor" in lower_q):
            match = re.search(r'\d+\.?\d*', answer)
            if match:
                budget = float(match.group())
        if "tipo" in lower_q or "modelo" in lower_q:
            car_type_preference = answer.strip()

    if num_passengers is None:
        num_passengers = 4  # padrão mínimo
    if budget is None:
        budget = 150.0  # padrão máximo
    if car_type_preference is None:
        car_type_preference = ""

    return num_passengers, budget, car_type_preference

def rental_car_mode(chat, client):
    """
    Modo de Aluguel de Carros.
    A IA gera perguntas de filtro para coletar os dados necessários para identificar 
    o veículo ideal para o cliente. A conversa ocorre em 3 rodadas.
    Ao final, os dados extraídos são usados para filtrar os carros e efetuar a reserva.
    Após o usuário escolher um carro, o sistema pergunta quantos dias deseja alugar o veículo,
    calcula o total e solicita confirmação para concluir a reserva ou voltar à seleção.
    Se o usuário responder algo sem sentido (como resposta vazia ou sem valor numérico para perguntas numéricas),
    a pergunta será repetida.
    """
    print("\nVocê entrou no modo de Aluguel de Carros com filtro generativo.")
    print("Irei fazer algumas perguntas para entender sua necessidade, apenas sobre os dados dos veículos.\n")
    
    conversation_history = ""
    answers = {}  # Armazena as perguntas e respostas

    NUM_ROUNDS = 3
    for i in range(NUM_ROUNDS):
        question = generate_filter_question(client, conversation_history)
        while True:
            print(f"\nCarAssistant: {question}")
            user_answer = input("Você: ").strip()
            if not user_answer:
                print("CarAssistant: Resposta inválida. Por favor, responda a pergunta.")
                continue
            # Se a pergunta pede o tipo de carro, validar se a resposta é uma das válidas.
            if ("sedan" in question.lower() and "hatch" in question.lower() and "suv" in question.lower()):
                valid_types = {"sedan", "hatch", "suv"}
                if user_answer.lower() not in valid_types:
                    print("CarAssistant: Resposta inválida. Por favor, informe um tipo válido: Sedan, Hatch ou SUV.")
                    continue
            # Se a pergunta exige um valor numérico (orçamento, diária ou passageiro), tente converter.
            if any(kw in question.lower() for kw in ["orçamento", "diária", "passageiro"]):
                try:
                    float(user_answer)
                except ValueError:
                    print("CarAssistant: Resposta inválida. Por favor, informe um valor numérico.")
                    continue
            break
        conversation_history += f"Pergunta: {question}\nResposta: {user_answer}\n"
        answers[question] = user_answer

    num_passengers, budget, car_type_preference = extract_filter_data(answers)
    
    all_cars = database.get_all_cars()
    filtered_cars = []
    for carro in all_cars:
        # Índices: 0: id, 1: marca, 2: modelo, 3: tipo, 4: diária, 5: passageiros, 6: combustível, 7: disponível
        if carro[5] >= num_passengers and carro[4] <= budget:
            if car_type_preference:
                if car_type_preference.lower() in carro[3].lower():
                    filtered_cars.append(carro)
            else:
                filtered_cars.append(carro)
                
    if not filtered_cars:
        print("\nCarAssistant: Desculpe, não encontramos carros que correspondam aos seus critérios.")
        return

    print("\nCarAssistant: Com base nas suas respostas, encontrei as seguintes opções:")
    for carro in filtered_cars:
        print(f"ID: {carro[0]}, {carro[1]} {carro[2]} - Tipo: {carro[3]}, Diária: R$ {carro[4]:.2f}, "
              f"Passageiros: {carro[5]}, Combustível: {carro[6]}")

    # Loop de seleção do carro e confirmação
    while True:
        choice = input("\nDigite o ID do carro que deseja alugar ou 'cancelar' para abortar: ").strip()
        if choice.lower() == 'cancelar':
            print("CarAssistant: Operação cancelada. Voltando ao menu principal.")
            return
        try:
            car_id = int(choice)
            selected_car = None
            for carro in filtered_cars:
                if carro[0] == car_id:
                    selected_car = carro
                    break
            if selected_car is None:
                print("CarAssistant: ID inválido. Por favor, escolha um dos IDs listados.")
                continue

            print(f"\nCarAssistant: Você selecionou o carro {selected_car[1]} {selected_car[2]}.")
            while True:
                print("CarAssistant: Por favor, informe o número de dias que deseja alugar o veículo:")
                days_input = input("Você: ").strip()
                if not days_input:
                    print("CarAssistant: Resposta inválida. Por favor, informe o número de dias.")
                    continue
                try:
                    rental_days = int(days_input)
                    if rental_days <= 0:
                        print("CarAssistant: Por favor, informe um número válido de dias (maior que 0).")
                        continue
                    break
                except ValueError:
                    print("CarAssistant: Entrada inválida. Por favor, informe o número de dias em formato numérico.")

            total_cost = rental_days * selected_car[4]
            print(f"CarAssistant: O valor total para {rental_days} dia(s) é de R$ {total_cost:.2f}.")

            while True:
                confirm = input("CarAssistant: Deseja confirmar a reserva? (Digite 'confirmar' para confirmar ou 'voltar' para escolher outro modelo): ").strip().lower()
                if confirm == "confirmar":
                    print("CarAssistant: Seu carro foi reservado com sucesso! Obrigado por escolher nossos serviços.")
                    print("\nResumo da sua reserva:")
                    print(f"  Carro: {selected_car[1]} {selected_car[2]}")
                    print(f"  Tipo: {selected_car[3]}")
                    print(f"  Assentos: {selected_car[5]}")
                    print(f"  Combustível: {selected_car[6]}")
                    print(f"  Diária: R$ {selected_car[4]:.2f}")
                    print(f"  Número de dias: {rental_days}")
                    print(f"  Valor total: R$ {total_cost:.2f}")
                    return
                elif confirm == "voltar":
                    print("CarAssistant: Vamos retornar à lista de opções. Por favor, escolha outro modelo.")
                    print("\nCarAssistant: Opções disponíveis:")
                    for carro in filtered_cars:
                        print(f"ID: {carro[0]}, {carro[1]} {carro[2]} - Tipo: {carro[3]}, Diária: R$ {carro[4]:.2f}, "
                              f"Passageiros: {carro[5]}, Combustível: {carro[6]}")
                    break  # Retorna para nova escolha do carro
                else:
                    print("CarAssistant: Resposta inválida. Por favor, digite 'confirmar' ou 'voltar'.")
        except ValueError:
            print("CarAssistant: Entrada inválida. Digite um número de ID ou 'cancelar'.")

def is_relevant_question(question):
    """
    Nesta versão, verificamos a relevância de uma pergunta para a CarMax utilizando uma lista de palavras-chave ampliada.
    Se a pergunta contiver termos como 'empresa', 'serviços', 'política', 'história', 'aluguel', 'carros', 'carmax',
    'anos', 'horário', 'abrem' ou 'funcionamento', consideramos a pergunta relevante.
    """
    relevant_keywords = [
        "empresa", "serviços", "política", "história", "aluguel", "carros", "carmax",
        "anos", "horário", "abrem", "funcionamento"
    ]
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in relevant_keywords)

def company_info_mode(chat, client):
    """
    Modo para dúvidas sobre a empresa.
    Permite que o usuário faça 3 perguntas sobre os serviços, políticas e histórico da CarMax.
    As respostas serão geradas exclusivamente com base no texto disponível em business_info,
    e o sistema responderá como se fosse um atendente da CarMax, usando a voz corporativa.
    Perguntas consideradas irrelevantes receberão uma resposta padrão e não serão incluídas no resumo final.
    """
    business = database.get_business_info()
    if business is None:
        print("CarAssistant: Informação da empresa não encontrada.")
        return

    company_name, info_text = business

    print("\nVocê entrou na área de Dúvidas sobre a Empresa.")
    print(f"\nBem-vindo à área de atendimento da {company_name}.")
    print("Você pode fazer perguntas sobre nossos serviços, políticas e histórico.\n")

    qas = {}

    for i in range(3):
        question = input(f"Pergunta {i+1}: ").strip()
        
        if not is_relevant_question(question):
            answer = (f"Como {company_name}, prezamos pela sua experiência conosco. No entanto, "
                      f"a sua pergunta sobre '{question}' não está relacionada aos nossos serviços de aluguel de carros. "
                      "Para informações sobre este assunto, sugerimos consultar outras fontes. Se precisar de ajuda com aluguel de veículos, estamos à disposição!")
            print(f"\nResposta: {answer}\n")
        else:
            prompt = (
                f"Você é um atendente da {company_name}. Responda a seguinte pergunta com base exclusivamente nas informações abaixo, "
                "utilizando a voz de representante da empresa (primeira pessoa do plural, por exemplo, 'nós', 'a CarMax').\n\n"
                f"Informações da empresa:\n{info_text}\n\n"
                f"Pergunta: {question}\n"
                "Resposta:"
            )
            response = client.models.generate_content(
                model=config.MODEL_ID,
                contents=[prompt],
                config=types.GenerateContentConfig(max_output_tokens=300, temperature=0.2)
            )
            answer = response.text
            print(f"\nResposta: {answer}\n")
            qas[question] = answer

    if qas:
        summary_prompt = "Baseado nas seguintes perguntas e respostas sobre a empresa, forneça um resumo dos principais pontos:\n"
        for idx, (q, a) in enumerate(qas.items(), start=1):
            summary_prompt += f"{idx}. Pergunta: {q}\n   Resposta: {a}\n"
        summary_prompt += "\nResumo:"
        summary_response = client.models.generate_content(
            model=config.MODEL_ID,
            contents=[summary_prompt],
            config=types.GenerateContentConfig(max_output_tokens=500, temperature=0.3)
        )
        print("\nResumo geral das suas dúvidas sobre a empresa:")
        print(summary_response.text)
    else:
        print("\nCarAssistant: Nenhuma pergunta relevante foi feita.")

def main():
    # Inicializa o cliente do Gemini e cria a sessão de chat.
    client = genai.Client(api_key=config.API_KEY)
    chat = client.chats.create(model=config.MODEL_ID)
    
    # Define o contexto inicial a partir das instruções do sistema.
    chat.send_message(config.SYSTEM_INSTRUCTION)
    
    print("Bem-vindo ao CarAssistant!")
    
    while True:
        print("\nMenu Principal:")
        print("1 - Alugar Carro")
        print("2 - Dúvidas sobre a Empresa")
        print("3 - Sair")
        choice_input = input("Escolha uma opção: ")
        choice = get_menu_option(choice_input)
        
        if choice == 1:
            rental_car_mode(chat, client)
        elif choice == 2:
            company_info_mode(chat, client)
        elif choice == 3:
            print("Obrigado por utilizar o CarAssistant!")
            break
        else:
            print("Opção inválida, tente novamente.")

if __name__ == "__main__":
    main()
