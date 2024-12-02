from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Initialize the chat model and tokenizer
model_name = "t5-small"
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

def get_response(user_message):
    # Tokenize the user's message
    inputs = tokenizer(
        "Chatbot: " + user_message,
        return_attention_mask=True,
        return_tensors="pt",
        padding="max_length",
        truncation=True,
        max_length=200,
        add_special_tokens=True
    )

    # Generate a response using the chat model
    outputs = model.generate(**inputs, max_length=200)

    # Convert the response to text
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Remove the prefix from the response
    response = response.replace("Chatbot: ", "", 1)

    return response

def main():
    print("Welcome to the chatbot!")
    while True:
        user_message = input("User: ")
        response = get_response(user_message)
        print("AI: ", response)

if __name__ == "__main__":
    main()