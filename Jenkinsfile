pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                // Pull the latest code from your GitHub repo
                git branch: 'master', url: 'https://github.com/pd1608/ANAproject.git'
            }
        }

        stage('Setup Python Environment') {
            steps {
                script {
                    echo "Setting up Python virtual environment..."
                    sh '''
                    cd /home/student/lab1/pythonscripts
                    # Create virtual environment if it doesn't exist
                    if [ ! -d "venv" ]; then
                        python3 -m venv venv
                    fi
                    # Activate venv and install dependencies
                    source venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    '''
                }
            }
        }

        stage('Ping Test') {
            steps {
                script {
                    echo "Running ping test for all devices in topology..."
                    sh '''
                    cd /home/student/lab1/pythonscripts
                    source venv/bin/activate
                    python3 ping_test.py > ping_results.txt
                    '''
                }
            }
        }

        stage('Results') {
            steps {
                script {
                    echo "Displaying ping results:"
                    sh 'cat /home/student/lab1/pythonscripts/ping_results.txt'
                    // Optional: archive the results in Jenkins
                    archiveArtifacts artifacts: '/home/student/lab1/pythonscripts/ping_results.txt'
                }
            }
        }
    }

    post {
        success {
            echo "✅ Ping test completed successfully!"
        }
        failure {
            echo "❌ Ping test failed!"
        }
    }
}
