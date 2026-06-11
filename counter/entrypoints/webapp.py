from io import BytesIO

from flask import Flask, request, jsonify

from counter import config


def create_app():

    app = Flask(__name__)

    count_action = config.get_count_action()
    get_predictions_action = config.get_predictions_action()

    @app.route('/object-count', methods=['POST'])
    def object_detection():
        threshold = float(request.form.get('threshold', 0.5))
        uploaded_file = request.files['file']
        image = BytesIO()
        uploaded_file.save(image)
        count_response = count_action.execute(image, threshold)
        return jsonify(count_response.to_dict())

    @app.route('/object-predictions', methods=['POST'])
    def object_predictions():
        threshold = float(request.form.get('threshold', 0.5))
        uploaded_file = request.files['file']
        image = BytesIO()
        uploaded_file.save(image)
        predictions = get_predictions_action.execute(image, threshold)
        return jsonify([p.to_dict() for p in predictions])

    return app


if __name__ == '__main__':
    app = create_app()
    app.run('0.0.0.0', debug=True)
