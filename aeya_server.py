import cv2
import flask
import os
import gmic
import numpy
import base64
import hashlib
import contextlib
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# Creating GMIC interpreter object
gmic_interpreter = gmic.Gmic()
app = flask.Flask(__name__)


def b64_to_cv2(base64_string):
    try:
        decoded_data = base64.b64decode(base64_string)
        hash_object = hashlib.sha256(decoded_data)
        r_hash = hash_object.hexdigest()
        img_arr = numpy.frombuffer(decoded_data , dtype=numpy.uint8)
        cv2_img = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
        return cv2_img, r_hash
    except Exception as e:
        print(f"b64_to_cv2 exeption: {e}")


def acquired_saver(data, root="./"):
    print("try cr dirs")
    time_dir_path = os.path.join(
        root,
        f"{data['Meta']['Research']}",
        f"{data['Meta']['Date']}",
        f"{data['Meta']['Time']}_{data['Meta']['Bacteria']}{data['Meta']['Code']}-{data['Meta']['Dilution']}{data['Meta']['Cell']}")

    images_dir_path = os.path.join(time_dir_path, "Images")
    source_dir_path = os.path.join(time_dir_path, "Source")
    source_b_data_dir_path = os.path.join(source_dir_path, "B")
    source_p_data_dir_path = os.path.join(source_dir_path, "P")

    os.makedirs(images_dir_path, exist_ok=True)
    os.makedirs(source_b_data_dir_path, exist_ok=True)
    os.makedirs(source_p_data_dir_path, exist_ok=True)

    link_b = os.path.join(images_dir_path, f"{data['Meta']['Time']}_B_{data['Meta']['Time']}_{data['Meta']['Bacteria']}{data['Meta']['Code']}-{data['Meta']['Dilution']}{data['Meta']['Cell']}.png")
    link_p = os.path.join(images_dir_path, f"{data['Meta']['Time']}_P_{data['Meta']['Time']}_{data['Meta']['Bacteria']}{data['Meta']['Code']}-{data['Meta']['Dilution']}{data['Meta']['Cell']}.png")
    link_mask = os.path.join(images_dir_path, f"{data['Meta']['Time']}_Mask_{data['Meta']['Time']}_{data['Meta']['Bacteria']}{data['Meta']['Code']}-{data['Meta']['Dilution']}{data['Meta']['Cell']}.png")
    print("try wr 1")
    print(link_b)
    cv2.imwrite(link_b, data["Images"]["B"])
    print("try wr 2")
    print(link_p)
    cv2.imwrite(link_p, data["Images"]["P"])
    print("try wr 3")
    try:
        cv2.imwrite(link_mask, data["Images"]["Mask"])
    except Exception as e:
        print(e)

    for light, values in data["Transport_Source"].items():
        for exposure, image in values.items():
            save_path = os.path.join(source_dir_path, light, f"{data['Meta']['Time']}_{light}_{data['Meta']['Bacteria']}{data['Meta']['Code']}-{data['Meta']['Dilution']}{data['Meta']['Cell']}_{exposure}.png")
            cv2.imwrite(save_path, image)

    return link_b, link_p, link_mask


def answer(data, b_link, p_link):
    answer_dict = {
        "Links": {
            "B": b_link,
            "P": p_link,
            "Mask": ""
        },
        "Lost_Hashes": []
    }
    return answer_dict


@app.route('/upload/', methods=['POST'])
def upload():
    data = flask.request.get_json()
    if not data:
        return "No JSON data provided", 400
    else:
        data["Images"]["B"], r_hash = b64_to_cv2(data["Images"]["B"])
        data["R_Hash"]["Images"]["B"] = r_hash
        data["Images"]["P"], r_hash = b64_to_cv2(data["Images"]["P"])
        data["R_Hash"]["Images"]["P"] = r_hash
        try:
            data["Images"]["Mask"], r_hash = b64_to_cv2(data["Images"]["Mask"])
            data["R_Hash"]["Images"]["Mask"] = r_hash
        except:
            pass

        for light, values in data["Transport_Source"].items():
            for exposure, b64_image in values.items():
                data["R_Hash"]["Source"][light].setdefault(exposure, None)
                data["Transport_Source"][light][exposure], r_hash = b64_to_cv2(b64_image)
                data["R_Hash"]["Source"][light][exposure] = r_hash

        if data["Gmic_check"] == "on":
            # gmic_image_list = []
            # gmic_image_list.append(gmic.GmicImage.from_numpy(data["Images"]["B"]))
            # gmic_image_list.append(gmic.GmicImage.from_numpy(data["Images"]["P"]))
            gmic_image_B = gmic.GmicImage.from_numpy(data["Images"]["B"])
            gmic_image_P = gmic.GmicImage.from_numpy(data["Images"]["P"])
            gmic_image_Mask = gmic.GmicImage.from_numpy(data["Images"]["Mask"])

            gmic_interpreter.run(f"{data['Gmic']}", gmic_image_B)
            gmic_interpreter.run(f"{data['Gmic']}", gmic_image_P)
            gmic_interpreter.run("rotate 90", gmic_image_Mask)
            data["Images"]["B"] = gmic_image_B.to_numpy()
            data["Images"]["P"] = gmic_image_P.to_numpy()
            data["Images"]["Mask"] = gmic_image_Mask.to_numpy()
            data["Images"]["B"] = numpy.squeeze(data["Images"]["B"], axis=2)
            data["Images"]["P"] = numpy.squeeze(data["Images"]["P"], axis=2)
            data["Images"]["Mask"] = numpy.squeeze(data["Images"]["Mask"], axis=2)

        else:
            string_image_b = None
            string_image_p = None

        if data["Hash"] == data["R_Hash"]:
            print("Ok hash")
            print(data["Root"])
            link_b, link_p, link_mask = acquired_saver(data, root=data["Root"])

            answ = answer(data, link_b, link_p)
            return flask.jsonify(answ), 200
        else:
            return flask.jsonify(answer(data)), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1515, debug=False)
