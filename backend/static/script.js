// ================= IMAGE PREVIEW =================

function previewImage(input){

    const preview =
    document.getElementById("preview");

    if(input.files && input.files[0]){

        const reader =
        new FileReader();

        reader.onload = function(e){

            preview.src =
            e.target.result;

            preview.style.display =
            "block";
        };

        reader.readAsDataURL(
            input.files[0]
        );
    }
}

// ================= LOADER =================

document.addEventListener(
"DOMContentLoaded",
function(){

    const form =
    document.querySelector("form");

    if(form){

        form.addEventListener(
        "submit",
        function(){

            const loader =
            document.getElementById(
            "loader"
            );

            if(loader){

                loader.style.display =
                "flex";
            }
        });
    }
});

// ================= CAMERA =================

let cameraStream = null;

async function startCamera(){

    const video =
    document.getElementById(
    "video"
    );

    try{

        cameraStream =
        await navigator
        .mediaDevices
        .getUserMedia({
            video:true
        });

        video.srcObject =
        cameraStream;

        video.style.display =
        "block";

    }

    catch(error){

        alert(
        "Camera access denied or camera not available."
        );
    }
}

// ================= STOP CAMERA =================

function stopCamera(){

    if(cameraStream){

        cameraStream
        .getTracks()
        .forEach(track => {

            track.stop();

        });

        cameraStream = null;
    }

    const video =
    document.getElementById(
    "video"
    );

    if(video){

        video.style.display =
        "none";
    }
}

// ================= FILE TYPE CHECK =================

document.addEventListener(
"DOMContentLoaded",
function(){

    const fileInput =
    document.querySelector(
    'input[type="file"]'
    );

    if(fileInput){

        fileInput.addEventListener(
        "change",
        function(){

            const file =
            this.files[0];

            if(!file) return;

            const allowed = [

                "image/jpeg",
                "image/jpg",
                "image/png"

            ];

            if(
            !allowed.includes(
            file.type
            )){

                alert(
                "Only JPG, JPEG and PNG images are allowed."
                );

                this.value = "";

                return;
            }
        });
    }
});

// ================= FILE SIZE CHECK =================

document.addEventListener(
"DOMContentLoaded",
function(){

    const fileInput =
    document.querySelector(
    'input[type="file"]'
    );

    if(fileInput){

        fileInput.addEventListener(
        "change",
        function(){

            const file =
            this.files[0];

            if(!file) return;

            const maxSize =
            5 * 1024 * 1024;

            if(
            file.size > maxSize
            ){

                alert(
                "Image size must be less than 5 MB."
                );

                this.value = "";

                return;
            }
        });
    }
});

// ================= DRAG & DROP =================

document.addEventListener(
"DOMContentLoaded",
function(){

    const uploadBox =
    document.querySelector(
    ".upload-box"
    );

    const fileInput =
    document.querySelector(
    'input[type="file"]'
    );

    if(
    uploadBox &&
    fileInput
    ){

        uploadBox.addEventListener(
        "dragover",
        function(e){

            e.preventDefault();

            uploadBox.style.border =
            "2px dashed #2ecc71";
        });

        uploadBox.addEventListener(
        "dragleave",
        function(){

            uploadBox.style.border =
            "none";
        });

        uploadBox.addEventListener(
        "drop",
        function(e){

            e.preventDefault();

            uploadBox.style.border =
            "none";

            fileInput.files =
            e.dataTransfer.files;

            previewImage(
            fileInput
            );
        });
    }
});

// ================= HIDE LOADER =================

window.onload = function(){

    const loader =
    document.getElementById(
    "loader"
    );

    if(loader){

        loader.style.display =
        "none";
    }
};

// ================= AUTO SCROLL TO RESULT =================

window.addEventListener(
"load",
function(){

    const result =
    document.querySelector(
    ".result-card"
    );

    if(result){

        result.scrollIntoView({
            behavior:"smooth"
        });
    }
});

// ================= SUCCESS MESSAGE =================

console.log(
"Plant Disease Detection System Loaded Successfully"
);

// ================= THEME TOGGLE =================

function toggleTheme(){

    document.body.classList.toggle(
    "light-mode"
    );

    const btn =
    document.getElementById(
    "themeBtn"
    );

    if(
    document.body.classList.contains(
    "light-mode"
    )
    ){

        btn.innerHTML =
        "☀️ Light Mode";
    }

    else{

        btn.innerHTML =
        "🌙 Dark Mode";
    }
}