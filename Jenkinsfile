pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                // Pull the latest code from your GitHub repo
                git branch: 'main', url: 'https://github.com/pd1608/ANAproject.git'
            }
        }

        stage('Ping Test') {
            steps {
                script {
                echo "Running ping test for all devices in topology..."

                // Run your ping test Python script
                sh '''
                cd /home/student/lab1/pythonscripts
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
