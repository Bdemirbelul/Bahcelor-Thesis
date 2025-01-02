class PhysicsDataset:
    def __init__(self):
        self.data = {
            # Mechanics
            "newton's second law": {
                "definition": "Newton's second law states that the acceleration of an object is directly proportional to the net force acting on it and inversely proportional to its mass.",
                "formula": "F = ma"
            },
            "momentum": {
                "definition": "Momentum is the product of the mass and velocity of an object.",
                "formula": "p = mv"
            },
            "work": {
                "definition": "Work is defined as the transfer of energy when a force is applied over a distance.",
                "formula": "W = Fd cos(θ)"
            },
            "power": {
                "definition": "Power is the rate at which work is done or energy is transferred.",
                "formula": "P = W/t"
            },
            "conservation of energy": {
                "definition": "The law of conservation of energy states that energy cannot be created or destroyed, only transformed from one form to another.",
                "formula": ""
            },
            # Add more entries as needed...
        }

    def get_physics_answer(self, user_input):
        user_input = user_input.lower()  # Normalize input to lower case

        # Check for physics-related responses
        for question, answer in self.data.items():
            if question in user_input:
                # Check if the user is asking for a formula
                if "formula" in user_input:
                    return answer["formula"] if answer["formula"] else "No formula available."
                # Check if the user is asking for a definition
                elif "definition" in user_input or "what is" in user_input:
                    return answer["definition"]

                # If neither is specified, return both (or just one, depending on your choice)
                return f"{answer['definition']} Formula: {answer['formula']}" if answer["formula"] else answer["definition"]

        return 


