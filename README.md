# AWS Solutions Architect: The Problem Solver Game

An interactive educational game where players take on the role of AWS cloud architects, solving real-world problems presented by various NPCs. Built with Amazon Q CLI integration for AI-powered hints and guidance.

## 🎮 Game Overview

Players interact with different characters (startup CEOs, data analysts, security officers, developers) who present AWS-related challenges. Solve problems through multiple-choice questions based on real AWS certification scenarios, with AI assistance from Amazon Q CLI.

## 🚀 Features

- **Interactive NPC System**: Engage with diverse characters presenting real business scenarios
- **AWS Certification-Style Questions**: 70+ questions covering EC2, S3, RDS, VPC, Lambda, and more
- **AI-Powered Hints**: Amazon Q CLI integration for intelligent guidance
- **Progressive Difficulty**: From junior to principal architect levels
- **Scoring & Leaderboard**: Track progress and compete with others
- **Real-time Feedback**: Detailed explanations and AWS best practices

## 🛠 Technology Stack

### Backend
- **AWS Lambda**: Serverless backend functions
- **Amazon DynamoDB**: User data and game state storage
- **Amazon API Gateway**: RESTful API endpoints
- **Amazon Q CLI**: AI-powered hint system

### Frontend
- **HTML5/CSS3/JavaScript**: Core web technologies
- **Phaser.js**: 2D game engine for interactive elements
- **Responsive Design**: Works on desktop and mobile

## 📁 Project Structure

```
aws-problem-solver-game/
├── src/
│   ├── lambda_functions/     # AWS Lambda functions
│   ├── api/                  # API layer
│   ├── frontend/             # Web interface
│   ├── game_data/           # Questions and NPC data
│   └── utils/               # Utility functions
├── infrastructure/          # AWS infrastructure as code
├── tests/                   # Test files
└── docs/                    # Documentation
```

## 🏗 Development Status

This project is currently under development. Check the [TASK_LIST.md](TASK_LIST.md) for detailed progress tracking.

### Current Phase: Phase 1 - Project Setup ✅
- [x] Basic directory structure
- [x] Package configuration
- [x] Git setup
- [ ] AWS infrastructure setup
- [ ] Amazon Q CLI integration

## 🚦 Getting Started

### Prerequisites
- Python 3.9+
- AWS CLI v2 with Amazon Q CLI
- AWS Account with appropriate permissions
- Node.js (for frontend dependencies)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd aws-problem-solver-game

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your AWS configuration
```

### Running Locally
```bash
# Start the development server
npm start

# Run tests
npm test
```

## 🎯 Game Characters

### Alex - Startup CEO
*"Our website traffic just increased 10x and the server crashed!"*
- **Focus**: Auto Scaling, Load Balancers, CloudWatch
- **Difficulty**: Beginner to Intermediate

### Sarah - Data Analyst
*"I need to analyze 100GB of log data daily, but it's too slow!"*
- **Focus**: EMR, Redshift, Athena, S3
- **Difficulty**: Intermediate to Advanced

### Mike - Security Officer
*"How can we strengthen our database security?"*
- **Focus**: IAM, VPC, Security Groups, KMS
- **Difficulty**: Intermediate

### Jenny - Developer
*"I want to build a serverless API, which services should I use?"*
- **Focus**: Lambda, API Gateway, DynamoDB
- **Difficulty**: Beginner to Intermediate

## 📊 Learning Outcomes

After playing this game, you'll be better prepared for:
- AWS Solutions Architect certification exams
- Real-world cloud architecture decisions
- AWS best practices and cost optimization
- Problem-solving in cloud environments

## 🤝 Contributing

This project is part of the AWS Community Event. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- AWS Community for the inspiration
- Amazon Q CLI team for the AI integration
- AWS documentation and certification guides
- Beta testers and contributors

---

**Built with ❤️ for the AWS Community Event**
